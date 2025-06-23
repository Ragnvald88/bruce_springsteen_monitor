# Example Ticket Filter Configurations

## Bruce Springsteen Concert Examples

### Target Only Prato A (Best Standing Area)
Filters: `Prato A`
Mode: ANY

### Target Multiple Prato Sections
Filters: `Prato A, Prato B, Prato C`
Mode: ANY

### Target Only Gold/VIP Sections
Filters: `Gold, VIP, Premium`
Mode: ANY

### Target Specific Tribune
Filters: `Tribuna Est`
Mode: ANY

### Target Close Sectors Only
Filters: `Settore 1, Settore 2, Settore 3`
Mode: ANY

### Avoid Certain Areas (using ALL mode)
If ticket descriptions include both section AND location:
Filters: `Tribuna, Centrale`
Mode: ALL
(This would only accept "Tribuna Centrale" tickets)

## Tips

1. Run "Test Filters" first to see actual ticket text
2. Italian section names are case-insensitive
3. Partial matches work (e.g., "Prato" matches "Prato A", "Prato B", etc.)
4. Be specific to avoid unwanted sections
5. Check the log file to see why tickets were filtered

## Common Section Priority (Best to Worst)

1. **Prato A/B** - Front standing areas
2. **Parterre** - Floor seating
3. **Tribuna Centrale** - Central tribune
4. **First Ring Sectors** - Lower numbered sectors
5. **Upper Tribuna** - Higher sections
6. **Prato C/D** - Far standing areas
