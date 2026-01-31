import streamlit as st
from PIL import Image
import zipfile
import io
import os
from datetime import datetime
from collections import Counter

def show():
    st.markdown('<div class="title">Image Resizer</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Resize images to 1000x1000 with smart padding</div>', unsafe_allow_html=True)
    
    # Info section
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                border-radius: 15px; padding: 1.5rem; color: white; margin-bottom: 1.5rem;">
        <div style="font-size: 1.2rem; font-weight: 600; margin-bottom: 1rem;">How It Works</div>
        <div style="font-size: 0.95rem; line-height: 1.6;">
            Upload single or multiple images. All images will be resized to exactly 1000x1000 pixels 
            while maintaining aspect ratio. Smart padding automatically detects and uses the background 
            color from image edges.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Upload section
    uploaded_files = st.file_uploader(
        "Upload Images",
        type=['png', 'jpg', 'jpeg', 'bmp', 'tiff'],
        accept_multiple_files=True,
        help="Select one or more images to resize"
    )
    
    if uploaded_files:
        st.info(f"Uploaded {len(uploaded_files)} image(s)")
        
        if st.button("Resize Images", use_container_width=True):
            with st.spinner("Processing images..."):
                try:
                    # Create temporary directory
                    temp_dir = f"resized_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    os.makedirs(temp_dir, exist_ok=True)
                    
                    processed_files = []
                    gallery_images = []
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    for idx, uploaded_file in enumerate(uploaded_files):
                        progress_bar.progress((idx + 1) / len(uploaded_files))
                        status_text.text(f"Processing {idx + 1} of {len(uploaded_files)}...")
                        
                        # Open image
                        img = Image.open(uploaded_file)
                        
                        # Convert to RGB if needed
                        if img.mode == 'RGBA':
                            bg = Image.new('RGB', img.size, (255, 255, 255))
                            bg.paste(img, mask=img.split()[3])
                            img = bg
                        elif img.mode != 'RGB':
                            img = img.convert('RGB')
                        
                        # Resize image
                        resized_img = resize_image_with_padding(img, (1000, 1000))
                        
                        # Save resized image
                        original_filename = uploaded_file.name
                        base_name = os.path.splitext(original_filename)[0]
                        file_extension = os.path.splitext(original_filename)[1]
                        
                        if file_extension.lower() in ['.jpg', '.jpeg']:
                            output_filename = original_filename
                        else:
                            output_filename = f"{base_name}.jpg"
                        
                        output_path = os.path.join(temp_dir, output_filename)
                        resized_img.save(output_path, 'JPEG', quality=95, optimize=True)
                        
                        processed_files.append(output_path)
                        gallery_images.append(resized_img)
                    
                    progress_bar.empty()
                    status_text.empty()
                    
                    st.success(f"Successfully resized {len(processed_files)} images!")
                    
                    # Create metrics
                    col1, col2, col3 = st.columns(3)
                    
                    metric_style = """
                    <div style="background: #f9fafb; border-radius: 10px; padding: 1.5rem; 
                                text-align: center; border: 2px solid #e5e7eb;">
                        <div style="font-size: 2rem; font-weight: 700; color: #667eea;">{}</div>
                        <div style="color: #6b7280; font-size: 0.9rem; margin-top: 0.5rem;">{}</div>
                    </div>
                    """
                    
                    with col1:
                        st.markdown(metric_style.format(len(processed_files), "Images Processed"), unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown(metric_style.format("1000x1000", "Output Size"), unsafe_allow_html=True)
                    
                    with col3:
                        total_size = sum(os.path.getsize(f) for f in processed_files)
                        size_mb = total_size / (1024 * 1024)
                        st.markdown(metric_style.format(f"{size_mb:.1f}MB", "Total Size"), unsafe_allow_html=True)
                    
                    st.markdown("---")
                    
                    # Download options
                    st.markdown("### Download Options")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Create ZIP file
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                            for file_path in processed_files:
                                zip_file.write(file_path, os.path.basename(file_path))
                        
                        zip_buffer.seek(0)
                        
                        st.download_button(
                            "Download All (ZIP)",
                            data=zip_buffer,
                            file_name=f"resized_images_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                            mime="application/zip",
                            use_container_width=True
                        )
                    
                    with col2:
                        if len(processed_files) == 1:
                            with open(processed_files[0], 'rb') as f:
                                st.download_button(
                                    "Download Image",
                                    data=f.read(),
                                    file_name=os.path.basename(processed_files[0]),
                                    mime="image/jpeg",
                                    use_container_width=True
                                )
                    
                    # Gallery preview
                    st.markdown("---")
                    st.markdown("### Preview Gallery")
                    
                    # Display images in grid
                    cols = st.columns(4)
                    for idx, img in enumerate(gallery_images):
                        with cols[idx % 4]:
                            st.image(img, use_container_width=True)
                            st.caption(os.path.basename(processed_files[idx]))
                    
                    # Cleanup
                    import shutil
                    try:
                        shutil.rmtree(temp_dir)
                    except:
                        pass
                
                except Exception as e:
                    st.error(f"Error processing images: {e}")
                    import traceback
                    st.code(traceback.format_exc())

def get_dominant_edge_color(img):
    """Detect the most common background color from corners and edges"""
    width, height = img.size
    
    # Sample pixels from the four corners
    corner_size = min(50, width // 5, height // 5)
    corner_pixels = []
    
    # Top-left corner
    tl = img.crop((0, 0, corner_size, corner_size))
    corner_pixels.extend(list(tl.getdata()))
    
    # Top-right corner
    tr = img.crop((width - corner_size, 0, width, corner_size))
    corner_pixels.extend(list(tr.getdata()))
    
    # Bottom-left corner
    bl = img.crop((0, height - corner_size, corner_size, height))
    corner_pixels.extend(list(bl.getdata()))
    
    # Bottom-right corner
    br = img.crop((width - corner_size, height - corner_size, width, height))
    corner_pixels.extend(list(br.getdata()))
    
    # Count color frequencies
    color_counts = Counter(corner_pixels)
    
    # Get the most common color
    if color_counts:
        most_common_color = color_counts.most_common(1)[0][0]
        return most_common_color
    
    return (255, 255, 255)  # Default to white

def resize_image_with_padding(img, size=(1000, 1000)):
    """Resize image to exact 1000x1000 with smart padding"""
    target_width, target_height = size
    
    # Convert to RGB if needed
    if img.mode == 'RGBA':
        bg = Image.new('RGB', img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[3])
        img = bg
    elif img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Detect the dominant edge color for padding
    padding_color = get_dominant_edge_color(img)
    
    # Create background with detected color
    new_img = Image.new('RGB', size, padding_color)
    
    # Calculate scaling to fit image inside 1000x1000
    img_copy = img.copy()
    img_copy.thumbnail(size, Image.LANCZOS)
    
    # Calculate position to center the image
    x = (target_width - img_copy.width) // 2
    y = (target_height - img_copy.height) // 2
    
    # Paste the resized image onto the background
    new_img.paste(img_copy, (x, y))
    
    return new_img
