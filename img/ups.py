import cv2
from cv2 import dnn_superres
import time
image = 0
prevImg = 0

#time.sleep(1)
# Create an SR object
sr = dnn_superres.DnnSuperResImpl_create()

# Read image
#while(image == prevImg):
image = cv2.imread('./image.jpg')

#prevImg = image
# Read the desired model
path = 'ESPCN_x3.pb'
sr.readModel(path)

# Set the desired model and scale to get correct pre- and post-processing
sr.setModel("espcn", 3)

# Upscale the image
result = sr.upsample(image)

# Save the image
cv2.imwrite("./image.jpg", result)