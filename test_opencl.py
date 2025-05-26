import cv2
import numpy as np

print(f"OpenCV version: {cv2.__version__}")

# Check if OpenCL is available
has_ocl = cv2.ocl.haveOpenCL()
print(f"cv2.ocl.haveOpenCL(): {has_ocl}")

if has_ocl:
    print("OpenCL is available. Trying to enable it...")
    cv2.ocl.setUseOpenCL(True)
    print(f"cv2.ocl.useOpenCL() after setting True: {cv2.ocl.useOpenCL()}")

    # More detailed OpenCL context info
    try:
        if cv2.ocl.useOpenCL(): # Re-check if it was successfully enabled
            platforms = cv2.ocl.getPlatfoms() # Note: Typo in OpenCV, should be getPlatforms()
            if not platforms: # If getPlatfoms is empty, try the correct spelling
                 if hasattr(cv2.ocl, 'getPlatforms'):
                      platforms = cv2.ocl.getPlatforms()


            print(f"Number of OpenCL platforms: {len(platforms)}")
            for i, platform in enumerate(platforms):
                print(f"  Platform #{i} Name: {platform.name()}")
                print(f"  Platform #{i} Vendor: {platform.vendor()}")
                print(f"  Platform #{i} Version: {platform.version()}")
                print(f"  Platform #{i} Device Count: {platform.deviceCount()}")
                for j in range(platform.deviceCount()):
                    device = platform.device(j)
                    print(f"    Device #{j} Name: {device.name()}")
                    print(f"    Device #{j} Type: {device.type()}") # e.g., DEVICE_TYPE_GPU
                    print(f"    Device #{j} OpenCL C Version: {device.OpenCL_C_Version()}")
                    print(f"    Device #{j} Available: {device.available()}")
            

            # Try a simple UMat operation
            print("Attempting to create a UMat (OpenCL matrix)...")
            try:
                arr = np.random.randint(0, 256, (100, 100), dtype=np.uint8)
                umat = cv2.UMat(arr)
                # Perform a simple operation that might use OpenCL
                umat_blurred = cv2.GaussianBlur(umat, (5,5), 0)
                result_arr = umat_blurred.get() # Convert back to numpy array
                if result_arr is not None:
                    print("UMat creation and GaussianBlur operation successful.")
                else:
                    print("UMat operation failed to produce a result.")
            except Exception as e:
                print(f"Error during UMat operation: {e}")
        else:
            print("OpenCL was reported as available but could not be enabled.")

    except Exception as e:
        print(f"Error getting OpenCL platform details or during UMat test: {e}")
        print("This might happen if the OpenCV build has limited OpenCL introspection capabilities or runtime issues.")

else:
    print("OpenCL is not available according to OpenCV.")

print("Test script finished.") 