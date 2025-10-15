"""
Progress tracking and checkpoint system for Azure Migration Tool
Allows resuming validation from the last successful checkpoint
"""
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from rich.console import Console
from rich.progress import Progress, TaskID
from rich.table import Table

from ..core.models import ValidationResult, ValidationStage

console = Console()


@dataclass
class ValidationCheckpoint:
    """Represents a validation checkpoint"""
    machine_name: str
    validation_stage: str
    status: str  # 'completed', 'failed', 'skipped'
    timestamp: str
    result_data: Dict[str, Any]
    execution_time_seconds: float


@dataclass 
class ProgressSession:
    """Represents a validation progress session"""
    session_id: str
    operation_type: str  # 'server_validation', 'lz_validation', etc.
    started_at: str
    last_updated: str
    total_machines: int
    completed_count: int
    failed_count: int
    skipped_count: int
    checkpoints: List[ValidationCheckpoint]
    config_file_hash: str  # Hash of input file to detect changes
    
    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage"""
        if self.total_machines == 0:
            return 0.0
        return (self.completed_count + self.failed_count + self.skipped_count) / self.total_machines * 100
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate of completed validations"""
        processed = self.completed_count + self.failed_count
        if processed == 0:
            return 0.0
        return self.completed_count / processed * 100


class ProgressTracker:
    """Manages validation progress tracking and checkpointing"""
    
    def __init__(self, workspace_path: Optional[Path] = None):
        self.workspace_path = workspace_path or Path.cwd() / ".azmig_progress"
        self.workspace_path.mkdir(exist_ok=True)
        self.current_session: Optional[ProgressSession] = None
        self.progress_bar: Optional[Progress] = None
        self.main_task: Optional[TaskID] = None
        
    def start_new_session(
        self, 
        operation_type: str, 
        total_machines: int,
        config_file_path: str
    ) -> ProgressSession:
        """Start a new validation session"""
        
        # Calculate file hash to detect config changes
        config_hash = self._calculate_file_hash(config_file_path)
        
        session = ProgressSession(
            session_id=datetime.now().strftime("%Y%m%d_%H%M%S"),
            operation_type=operation_type,
            started_at=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat(),
            total_machines=total_machines,
            completed_count=0,
            failed_count=0,
            skipped_count=0,
            checkpoints=[],
            config_file_hash=config_hash
        )
        
        self.current_session = session
        self._save_session()
        
        console.print(f"[cyan]📊 Started new validation session:[/cyan] {session.session_id}")
        console.print(f"[dim]Total machines to validate:[/dim] {total_machines}")
        
        return session
    
    def find_resumable_session(self, config_file_path: str, operation_type: str) -> Optional[ProgressSession]:
        """Find the most recent resumable session for the given configuration"""
        
        config_hash = self._calculate_file_hash(config_file_path)
        
        # Look for recent sessions (within last 7 days)
        cutoff_date = datetime.now() - timedelta(days=7)
        resumable_sessions = []
        
        for session_file in self.workspace_path.glob("session_*.json"):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                session_date = datetime.fromisoformat(session_data['started_at'])
                
                # Check if session is recent, same operation type, and same config
                if (session_date > cutoff_date and 
                    session_data['operation_type'] == operation_type and
                    session_data['config_file_hash'] == config_hash):
                    
                    session = ProgressSession(**session_data)
                    # Only consider if not fully completed
                    if session.completion_percentage < 100:
                        resumable_sessions.append(session)
                        
            except (json.JSONDecodeError, KeyError, ValueError):
                continue
        
        # Return most recent resumable session
        if resumable_sessions:
            return max(resumable_sessions, key=lambda s: datetime.fromisoformat(s.started_at))
        
        return None
    
    def resume_session(self, session: ProgressSession) -> bool:
        """Resume an existing validation session"""
        self.current_session = session
        
        console.print(f"[green]🔄 Resuming validation session:[/green] {session.session_id}")
        console.print(f"[dim]Started:[/dim] {session.started_at}")
        console.print(f"[dim]Progress:[/dim] {session.completion_percentage:.1f}% complete")
        console.print(f"[dim]Completed:[/dim] {session.completed_count}/{session.total_machines} machines")
        
        if session.failed_count > 0:
            console.print(f"[yellow]Previous failures:[/yellow] {session.failed_count} machines")
        
        return True
    
    def add_checkpoint(
        self, 
        machine_name: str, 
        validation_stage: ValidationStage,
        validation_result: ValidationResult,
        execution_time: float
    ):
        """Add a validation checkpoint"""
        if not self.current_session:
            return
            
        checkpoint = ValidationCheckpoint(
            machine_name=machine_name,
            validation_stage=validation_stage.value,
            status='completed' if validation_result.passed else 'failed',
            timestamp=datetime.now().isoformat(),
            result_data={
                'passed': validation_result.passed,
                'message': validation_result.message,
                'details': validation_result.details
            },
            execution_time_seconds=execution_time
        )
        
        self.current_session.checkpoints.append(checkpoint)
        
        # Update counters
        if validation_result.passed:
            self.current_session.completed_count += 1
        else:
            self.current_session.failed_count += 1
            
        self.current_session.last_updated = datetime.now().isoformat()
        
        # Update progress bar
        if self.progress_bar and self.main_task:
            completed = self.current_session.completed_count + self.current_session.failed_count
            self.progress_bar.update(self.main_task, completed=completed)
        
        # Save progress periodically (every 5 checkpoints)
        if len(self.current_session.checkpoints) % 5 == 0:
            self._save_session()
    
    def is_machine_completed(self, machine_name: str) -> bool:
        """Check if a machine has already been validated in current session"""
        if not self.current_session:
            return False
            
        return any(
            cp.machine_name == machine_name and cp.status in ['completed', 'failed']
            for cp in self.current_session.checkpoints
        )
    
    def get_machine_result(self, machine_name: str) -> Optional[ValidationResult]:
        """Get previous validation result for a machine"""
        if not self.current_session:
            return None
            
        for checkpoint in reversed(self.current_session.checkpoints):
            if checkpoint.machine_name == machine_name:
                return ValidationResult(
                    stage=ValidationStage(checkpoint.validation_stage),
                    passed=checkpoint.result_data['passed'],
                    message=checkpoint.result_data['message'],
                    details=checkpoint.result_data.get('details', {})
                )
        
        return None
    
    def start_progress_display(self):
        """Start the visual progress display"""
        if not self.current_session:
            return
            
        self.progress_bar = Progress()
        self.progress_bar.start()
        
        self.main_task = self.progress_bar.add_task(
            f"[cyan]Validating {self.current_session.operation_type}",
            total=self.current_session.total_machines
        )
        
        # Set initial progress if resuming
        completed = self.current_session.completed_count + self.current_session.failed_count
        self.progress_bar.update(self.main_task, completed=completed)
    
    def stop_progress_display(self):
        """Stop the visual progress display"""
        if self.progress_bar:
            self.progress_bar.stop()
            self.progress_bar = None
            self.main_task = None
    
    def display_session_summary(self):
        """Display summary of current validation session"""
        if not self.current_session:
            return
            
        console.print(f"\n[bold]📊 Validation Session Summary[/bold]")
        
        # Summary table
        table = Table(show_header=False, box=None)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")
        
        table.add_row("Session ID", self.current_session.session_id)
        table.add_row("Operation", self.current_session.operation_type.replace('_', ' ').title())
        table.add_row("Started", datetime.fromisoformat(self.current_session.started_at).strftime("%Y-%m-%d %H:%M:%S"))
        table.add_row("Duration", self._format_duration())
        table.add_row("", "")  # Spacer
        table.add_row("Total Machines", str(self.current_session.total_machines))
        table.add_row("[green]Completed[/green]", f"[green]{self.current_session.completed_count}[/green]")
        table.add_row("[red]Failed[/red]", f"[red]{self.current_session.failed_count}[/red]")
        table.add_row("[yellow]Skipped[/yellow]", f"[yellow]{self.current_session.skipped_count}[/yellow]")
        table.add_row("", "")  # Spacer
        table.add_row("Completion", f"{self.current_session.completion_percentage:.1f}%")
        table.add_row("Success Rate", f"{self.current_session.success_rate:.1f}%")
        
        console.print(table)
        
        # Performance metrics
        if self.current_session.checkpoints:
            avg_time = sum(cp.execution_time_seconds for cp in self.current_session.checkpoints) / len(self.current_session.checkpoints)
            console.print(f"\n[dim]Average validation time:[/dim] {avg_time:.2f}s per machine")
            
            # Estimate remaining time
            remaining = self.current_session.total_machines - (self.current_session.completed_count + self.current_session.failed_count)
            if remaining > 0:
                estimated_remaining = remaining * avg_time / 60  # Convert to minutes
                console.print(f"[dim]Estimated time remaining:[/dim] {estimated_remaining:.1f} minutes")
    
    def finalize_session(self):
        """Mark session as complete and clean up"""
        if not self.current_session:
            return
            
        self.current_session.last_updated = datetime.now().isoformat()
        self._save_session()
        
        console.print(f"\n[green]✅ Validation session completed:[/green] {self.current_session.session_id}")
        self.display_session_summary()
        
        self.current_session = None
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate hash of configuration file to detect changes"""
        import hashlib
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except FileNotFoundError:
            return ""
    
    def _save_session(self):
        """Save current session to disk"""
        if not self.current_session:
            return
            
        session_file = self.workspace_path / f"session_{self.current_session.session_id}.json"
        
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(self.current_session), f, indent=2, ensure_ascii=False)
    
    def _format_duration(self) -> str:
        """Format session duration in human-readable format"""
        if not self.current_session:
            return "N/A"
            
        start_time = datetime.fromisoformat(self.current_session.started_at)
        end_time = datetime.fromisoformat(self.current_session.last_updated)
        duration = end_time - start_time
        
        hours, remainder = divmod(duration.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        elif minutes > 0:
            return f"{int(minutes)}m {int(seconds)}s"
        else:
            return f"{int(seconds)}s"
    
    def cleanup_old_sessions(self, days_to_keep: int = 30):
        """Clean up old session files"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cleaned_count = 0
        
        for session_file in self.workspace_path.glob("session_*.json"):
            try:
                file_time = datetime.fromtimestamp(session_file.stat().st_mtime)
                if file_time < cutoff_date:
                    session_file.unlink()
                    cleaned_count += 1
            except (OSError, ValueError):
                continue
        
        if cleaned_count > 0:
            console.print(f"[dim]Cleaned up {cleaned_count} old session file(s)[/dim]")