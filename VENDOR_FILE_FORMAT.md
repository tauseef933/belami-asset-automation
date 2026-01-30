# Vendor Data File Format Specification

This document describes the expected format for vendor data files used with the Belami Asset Template Automation tool.

## File Requirements

### Basic Requirements
- **Format**: Excel (.xlsx or .xls)
- **Sheet Name**: One of the following (searched in order):
  1. "Entities"
  2. "All"
  3. "Sheet1"
  4. Or the first sheet if none of the above exist

### Required Columns

The vendor file must contain columns that match these patterns (case-insensitive):

#### SKU/Product Identifier
At least one column with a name containing:
- "sku"
- "item"
- "product"

Examples:
- "SKU"
- "Product SKU"
- "Item Number"
- "Product Code"

#### Image/Photo URLs or Filenames
At least one column with a name containing:
- "image"
- "photo"
- "url"

Examples:
- "Image URL"
- "Product Image"
- "Photo Link"
- "Image 1"
- "Main Image URL"

### Data Format

#### SKU Column
- Should contain unique product identifiers
- Format: Any text/number combination
- Examples: "3000-LCB", "ABC123", "PROD-001"
- Empty rows will be skipped

#### Image Columns
- Can contain:
  - Full URLs (e.g., "https://example.com/images/product.jpg")
  - Relative paths (e.g., "images/product.jpg")
  - Filenames (e.g., "product.jpg")
- Multiple images can be:
  - In separate columns (Image 1, Image 2, etc.)
  - In one cell separated by commas, semicolons, or newlines
- Supported formats: .jpg, .jpeg, .png, .gif, .pdf
- Video files (.mp4, .mov, .avi, .wmv, YouTube links) are automatically skipped

## Example File Structure

### Example 1: Simple Format

| SKU      | Product Name          | Image URL                                    |
|----------|----------------------|----------------------------------------------|
| 3000-LCB | LED Cabinet Light    | https://vendor.com/images/3000-LCB.jpg      |
| 3001-WH  | Wall Sconce White    | https://vendor.com/images/3001-WH.jpg       |
| 3002-BK  | Wall Sconce Black    | https://vendor.com/images/3002-BK.jpg       |

### Example 2: Multiple Image Columns

| Product SKU | Main Image               | Additional Image 1        | Additional Image 2        | Spec Sheet            |
|-------------|-------------------------|---------------------------|---------------------------|-----------------------|
| 3000-LCB    | 3000-LCB-main.jpg       | 3000-LCB-angle.jpg        | 3000-LCB-detail.jpg       | 3000-LCB-specs.pdf    |
| 3001-WH     | 3001-WH-main.jpg        | 3001-WH-lifestyle.jpg     |                           | 3001-WH-specs.pdf     |
| 3002-BK     | 3002-BK-main.jpg        |                           |                           | 3002-BK-specs.pdf     |

### Example 3: Multiple Images in One Cell

| Item Code | Product Images                                              |
|-----------|-------------------------------------------------------------|
| 3000-LCB  | 3000-LCB-main.jpg, 3000-LCB-angle.jpg, 3000-LCB-specs.pdf |
| 3001-WH   | 3001-WH-main.jpg; 3001-WH-lifestyle.jpg                    |
| 3002-BK   | 3002-BK-main.jpg                                           |

## Processing Logic

### Image Order and Classification

1. **First Image per SKU**
   - Automatically becomes `main_product_image`
   - Should be white background, full product view
   - Path: `brand/products/filename_new_1k.jpg`

2. **Additional Images**
   - Classified as `media`
   - MediaType determined by filename keywords:
     - "lifestyle", "room", "environment" → lifestyle
     - "dimension", "measurement", "drawing" → dimension
     - "detail", "closeup" → detail
     - "angle", "view" → angle
     - "swatch", "color", "finish" → swatch
     - "chart", "info", "callout" → informational
     - Default → detail
   - Path: `brand/media/filename_new_1k.jpg`

3. **PDF Files**
   - "install" in filename → `install_sheet`
   - Otherwise → `spec_sheet`
   - Path: `brand/specsheets/filename_new.pdf`

### Filename Processing

Original filenames are cleaned as follows:
1. Extension removed
2. Spaces, commas, slashes replaced with underscores
3. Special characters removed (except underscore and hyphen)
4. Converted to lowercase
5. Suffix added:
   - Images: `_new_1k`
   - PDFs: `_specs`

**Examples:**
- `3000-LCB Main Photo.jpg` → `3000-lcb_main_photo_new_1k`
- `Product 123, Angle View.jpg` → `product_123_angle_view_new_1k`
- `Spec Sheet/Installation.pdf` → `spec_sheet_installation_specs`

## Common Issues

### Missing Required Columns
**Issue**: "No image columns found in vendor file"  
**Solution**: Ensure at least one column name contains "image", "photo", or "url"

**Issue**: "No SKU columns found in vendor file"  
**Solution**: Ensure at least one column name contains "sku", "item", or "product"

### Data Quality Issues

**Empty Cells**
- Empty SKU cells: Row is skipped
- Empty image cells: No asset created for that cell
- Partial data: Only valid SKU-image pairs are processed

**Special Characters in SKUs**
- SKUs are preserved as-is in product_reference
- Used in code/label generation with proper cleaning

**Invalid Image URLs**
- If URL extraction fails, filename is used directly
- Check processing log for any parsing issues

## Best Practices

### Before Processing
1. Review vendor file for completeness
2. Verify SKU format matches your system
3. Check that image URLs/filenames are accessible
4. Confirm main product images come first

### Column Naming
Use clear, standard column names:
- Good: "SKU", "Product SKU", "Main Image", "Image URL"
- Avoid: "Col1", "Data", "A", "Pictures"

### Data Organization
- One product per row
- Main image in first image column
- Additional images in subsequent columns or same cell
- Include spec sheets in dedicated column

### Quality Control
- Remove test/placeholder data
- Verify image file extensions
- Check for duplicate SKUs
- Ensure all required products have images

## Sample Template

You can use this structure for your vendor files:

```
| SKU      | Product Name              | Main Image URL        | Media Image 1         | Media Image 2         | Spec Sheet        |
|----------|---------------------------|-----------------------|-----------------------|-----------------------|-------------------|
| PROD-001 | Product Name 1            | prod-001-main.jpg     | prod-001-angle.jpg    | prod-001-detail.jpg   | prod-001-spec.pdf |
| PROD-002 | Product Name 2            | prod-002-main.jpg     | prod-002-lifestyle.jpg|                       | prod-002-spec.pdf |
```

## Support

If your vendor file format differs significantly from these examples:
1. Contact your development team
2. Provide a sample of your vendor file
3. Request format mapping or application updates
