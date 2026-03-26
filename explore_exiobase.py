"""
Quick exploration of EXIOBASE structure
Fetches minimal metadata to understand the database structure
"""
import pymrio

print("Downloading EXIOBASE metadata...")
print("Note: This will download a small dataset (~100MB) to inspect structure")
print("This may take a few minutes...\n")

# Download the smallest/most recent EXIOBASE3 data (pxp = product by product)
# Using year 2020, which is the most reliable according to docs
storage_folder = './data/raw/exiobase'
meta = pymrio.download_exiobase3(
    storage_folder=storage_folder,
    system='pxp',  # product by product
    years=2020,
)

print("Download complete!")
print("\nLoading EXIOBASE data...")
exio = pymrio.parse_exiobase3(path=f'{storage_folder}/IOT_2020_pxp.zip')

print("\n" + "="*60)
print("EXIOBASE3 STRUCTURE")
print("="*60)

print(f"\nNumber of regions: {len(exio.get_regions())}")
print(f"\nRegions (sample): {exio.get_regions()[:10]}")

print(f"\n\nNumber of sectors: {len(exio.get_sectors())}")
print(f"\nSectors (first 15):")
for i, sector in enumerate(exio.get_sectors()[:15], 1):
    print(f"  {i}. {sector}")

print(f"\n\nAvailable extensions/satellites:")
extensions = [attr for attr in dir(exio) if not attr.startswith('_') and hasattr(getattr(exio, attr), 'F')]
for ext in extensions:
    print(f"  - {ext}")

print(f"\n\nMain matrices available:")
print(f"  - Z (inter-industry flows): {exio.Z.shape if hasattr(exio, 'Z') and exio.Z is not None else 'Not loaded'}")
print(f"  - Y (final demand): {exio.Y.shape if hasattr(exio, 'Y') and exio.Y is not None else 'Not loaded'}")
print(f"  - A (technical coefficients): {exio.A.shape if hasattr(exio, 'A') and exio.A is not None else 'Not loaded'}")

# Check for waste-related extensions
print(f"\n\nLooking for waste-related extensions...")
for attr_name in dir(exio):
    if 'waste' in attr_name.lower() or 'material' in attr_name.lower():
        attr = getattr(exio, attr_name)
        if hasattr(attr, 'F'):
            print(f"\nFound extension: {attr_name}")
            print(f"  F matrix shape: {attr.F.shape}")
            print(f"  Stressor categories (first 10):")
            for i, idx in enumerate(attr.F.index[:10], 1):
                print(f"    {i}. {idx}")

# Also check the resource extension
if hasattr(exio, 'resource'):
    print(f"\nResource extension:")
    print(f"  F matrix shape: {exio.resource.F.shape}")
    print(f"  Sample stressors (first 10):")
    for i, idx in enumerate(exio.resource.F.index[:10], 1):
        print(f"    {i}. {idx}")

print("\n" + "="*60)
print("Sample saved to data/raw/exiobase/")
print("="*60)
