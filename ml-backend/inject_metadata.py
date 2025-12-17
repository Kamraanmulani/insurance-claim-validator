import piexif
from PIL import Image
from datetime import datetime

def inject_metadata(image_path):
    img = Image.open(image_path)
    
    # 1. Camera Info (0th IFD)
    zeroth_ifd = {
        piexif.ImageIFD.Make: u"Apple",
        piexif.ImageIFD.Model: u"iPhone 14 Pro",
        piexif.ImageIFD.Software: u"iOS 17.2"
    }
    
    # 2. Date/Time (Exif IFD)
    # Format: "YYYY:MM:DD HH:MM:SS"
    # Matching the claim date in test_preprocessing.py (2025-12-05)
    date_str = u"2025:12:05 14:30:00"
    exif_ifd = {
        piexif.ExifIFD.DateTimeOriginal: date_str,
        piexif.ExifIFD.DateTimeDigitized: date_str
    }
    
    # 3. GPS Info (GPS IFD)
    # Example: Times Square, NY (40.7580, -73.9855)
    def to_deg(value, loc):
        if value < 0:
            loc_value = loc[1]
        else:
            loc_value = loc[0]
        abs_value = abs(value)
        deg = int(abs_value)
        t1 = (abs_value - deg) * 60
        min = int(t1)
        sec = round((t1 - min) * 60 * 10000)
        return (deg, 1), (min, 1), (sec, 10000), loc_value

    lat_deg = to_deg(40.7580, ["N", "S"])
    lng_deg = to_deg(-73.9855, ["E", "W"])

    gps_ifd = {
        piexif.GPSIFD.GPSLatitudeRef: lat_deg[3],
        piexif.GPSIFD.GPSLatitude: (lat_deg[0], lat_deg[1], lat_deg[2]),
        piexif.GPSIFD.GPSLongitudeRef: lng_deg[3],
        piexif.GPSIFD.GPSLongitude: (lng_deg[0], lng_deg[1], lng_deg[2]),
    }

    exif_dict = {"0th": zeroth_ifd, "Exif": exif_ifd, "GPS": gps_ifd}
    exif_bytes = piexif.dump(exif_dict)
    
    # Save with new metadata
    img.save(image_path, exif=exif_bytes)
    print(f"✅ Injected metadata into {image_path}")

if __name__ == "__main__":
    inject_metadata("test_images/damaged_car.jpg")
