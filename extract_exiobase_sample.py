"""
Extract small data samples from EXIOBASE for inspection
"""
import pymrio
import pandas as pd

print("Loading EXIOBASE data...")
exio = pymrio.parse_exiobase3(path='./data/raw/exiobase/IOT_2020_pxp.zip')

# Extract sample of material flows (first 5 regions, first 10 sectors)
print("\nExtracting material extension sample...")
material_sample = exio.material.F.iloc[:20, :50]  # First 20 stressors, first 50 region-sectors
material_sample.to_csv('./data/processed/exiobase_material_sample.csv')
print(f"  Saved: exiobase_material_sample.csv ({material_sample.shape})")

# Extract sample of inter-industry flows
print("\nExtracting inter-industry flows sample...")
z_sample = exio.Z.iloc[:50, :50]  # First 50x50 region-sectors
z_sample.to_csv('./data/processed/exiobase_z_sample.csv')
print(f"  Saved: exiobase_z_sample.csv ({z_sample.shape})")

# List all material flow categories
print("\nExtracting all material flow categories...")
material_categories = pd.DataFrame({
    'stressor': exio.material.F.index,
    'unit': exio.material.unit.get('unit', 'kt') if hasattr(exio.material, 'unit') else 'kt'
})
material_categories.to_csv('./data/processed/exiobase_material_categories.csv', index=False)
print(f"  Saved: exiobase_material_categories.csv ({len(material_categories)} categories)")

# Extract region and sector lists
print("\nExtracting region and sector metadata...")
regions_df = pd.DataFrame({
    'region_code': exio.get_regions(),
    'region_name': exio.get_regions()  # Full names might be in metadata
})
regions_df.to_csv('./data/processed/exiobase_regions.csv', index=False)
print(f"  Saved: exiobase_regions.csv ({len(regions_df)} regions)")

sectors_df = pd.DataFrame({
    'sector_code': range(len(exio.get_sectors())),
    'sector_name': exio.get_sectors()
})
sectors_df.to_csv('./data/processed/exiobase_sectors.csv', index=False)
print(f"  Saved: exiobase_sectors.csv ({len(sectors_df)} sectors)")

# Summary
print("\n" + "="*60)
print("EXIOBASE SAMPLE EXTRACTION COMPLETE")
print("="*60)
print("\nGenerated files:")
print("  1. exiobase_material_sample.csv - Sample material flows")
print("  2. exiobase_z_sample.csv - Sample inter-industry transactions")
print("  3. exiobase_material_categories.csv - All material stressor categories")
print("  4. exiobase_regions.csv - All regions")
print("  5. exiobase_sectors.csv - All sectors")
print("\nThese show the structure and content of EXIOBASE3.")
