from skimage.morphology import label
print "imported measure successfully"
try:
    from skimage import filters
    print "imported filters"
except ImportError as exc:
    from skimage import filter as filters
    print "imported via exception"
import matplotlib.pyplot as plt
print "imported matplotlib"
import numpy as np

#n = 12
#l = 256
#np.random.seed(1)
#im = np.zeros((l, l))
#points = l * np.random.random((2, n ** 2))
#im[(points[0]).astype(np.int), (points[1]).astype(np.int)] = 1
#im = filters.gaussian_filter(im, sigma= l / (4. * n))
#blobs = im > 0.7 * im.mean()
blobs = cv.imread("~/",0)
all_labels = label(blobs)
blobs_labels = label(blobs, background=0)

plt.figure(figsize=(9, 3.5))
plt.subplot(131)
plt.imshow(blobs, cmap='gray')
plt.axis('off')
plt.subplot(132)
plt.imshow(all_labels, cmap='spectral')
plt.axis('off')
plt.subplot(133)
plt.imshow(blobs_labels, cmap='spectral')
plt.axis('off')

plt.tight_layout()
plt.show()
