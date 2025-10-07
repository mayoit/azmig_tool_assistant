"""
Output formatters for terminal display
"""
from .table_formatter import EnhancedTableFormatter

# Convenience exports from EnhancedTableFormatter
format_landing_zone_results = EnhancedTableFormatter.format_landing_zone_results
format_servers_results = EnhancedTableFormatter.format_servers_results
format_landing_zone_summary = EnhancedTableFormatter.format_landing_zone_summary
display_landing_zone_details = EnhancedTableFormatter.display_landing_zone_details

# Alternative names (backward compatibility)
format_layer1_results = EnhancedTableFormatter.format_layer1_results
format_layer2_results = EnhancedTableFormatter.format_layer2_results
format_layer1_summary = EnhancedTableFormatter.format_layer1_summary
display_layer1_details = EnhancedTableFormatter.display_layer1_details

__all__ = [
    'EnhancedTableFormatter',
    # Preferred functions
    'format_landing_zone_results',
    'format_servers_results',
    'format_landing_zone_summary',
    'display_landing_zone_details',
    # Alternative names
    'format_layer1_results',
    'format_layer2_results',
    'format_layer1_summary',
    'display_layer1_details',
]
