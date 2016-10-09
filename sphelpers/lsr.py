"""
@author: Jordan Graesser
Adapted from Anil Cheriyadat's MATLAB code
"""

try:
    from scipy.ndimage.measurements import label as lab_img
    from scipy.fftpack import fftshift, fft
    # from skimage.segmentation import find_boundaries, mark_boundaries
except ImportError:
    raise ImportError('SciPy.ndimage and/or .fftpack did not load')    
   
try:
    import numpy as np
except ImportError:
    raise ImportError('NumPy must be installed')

# try:
#     import numexpr as ne
# except:
#     raise ImportError('Numexpr must be installed')
    
try:
    import cv2
except ImportError:
    raise ImportError('OpenCV must be installed')

try:
    import matplotlib.pyplot as plt
except ImportError:
    raise ImportError('Matplotlib must be installed')

old_settings = np.seterr(all='ignore')

import warnings
warnings.filterwarnings("ignore")

global pi
pi = 3.14159265


def getEdgePixs(ori_img, mag_img, mag_thresh):

    """
    Ignore gradients with small magnitude
    """
    
    edge_pixs = np.where(mag_img.ravel() > mag_thresh)
    
    ori_img[(ori_img < 0)] += 360.
    
    return ori_img.ravel()[edge_pixs], edge_pixs


def img2_ori_edge(img):

    cArr = np.array([[-1, -1],
                    [1, 1]]).reshape(2, 2)
                    
    cArr_x = np.array([[-1, 1],
                       [-1, 1]]).reshape(2, 2)

    # compute gradient derivatives
    deriv_x = cv2.filter2D(img, -1, cArr_x, borderType=cv2.BORDER_CONSTANT)
    deriv_y = cv2.filter2D(img, -1, cArr, borderType=cv2.BORDER_CONSTANT)

    # compute gradient angle
    edge_ori = (180. / pi) * np.arctan2(deriv_y, (deriv_x + 1e-5))

    # compute gradient magnitude
    edge_mag = np.sqrt(np.add(np.power(deriv_x, 2.), np.power(deriv_y, 2.)))
    
    return edge_ori, edge_mag, deriv_x, deriv_y


class binQ():
    
    def __init__(self, data, edgePixs, lsr_thresh, dx, dy, rows, cols):

        self.bin(data, edgePixs, lsr_thresh, dx, dy, rows, cols)
    
    def bin(self, data, edgePixs, lsr_thresh, dx, dy, rows, cols):
    
        # Here we divide them into bins with bin boundaries as 
        # ... 0,45,90,135,180,225,270,315,0
        binidx = np.searchsorted(range(0, 360+45, 45), data)
        
        lsfim1 = np.zeros((2, rows, cols))		
        lsfarr = np.zeros((1, 6))
        
        for k in xrange(1, len(range(0, 360+45, 45))):  # the range is for 45, ..n, 360, by 45
        
            curr_bin = np.where(binidx == k)
            
            if len(curr_bin[0]):
                
                edge_img = np.zeros(rows*cols)
                edge_img[edgePixs[0][curr_bin[0]]] = 1
                
                edge_img = edge_img.reshape(rows, cols)
                
                # Extract LSR by grouping pixels with similar orientations
                lsfim1, lsfarr = self.generate_regions(edge_img, lsr_thresh, lsfim1, lsfarr, dx, dy, rows, cols)
                # lsfim1, lsfarr = _lineSupport.generate_regions(edge_img, lsr_thresh, lsfim1, lsfarr, dx, dy, rows, cols)
                

        # Here we divide them into bins with bin boundaries as    
        # ... 22.5,67.5,112.5,157.5,202.5,247.5,292.5,337.5,22.5    
        binidx = np.searchsorted(list(np.linspace(22.5, 360, num=np.floor((360-22.5)/45.))), data)
        
        lsfim2 = np.zeros((2, rows, cols))  
        
        for k in xrange(1, len(list(np.linspace(22.5, 360, num=np.floor((360-22.5)/45.))))): # the range is for 22.5, ..n, 337.5, by 45
        
            curr_bin = np.where(binidx == k)
            
            if len(curr_bin[0]):
                
                edge_img = np.zeros(rows*cols)
                edge_img[edgePixs[0][curr_bin[0]]] = 1
                
                edge_img = edge_img.reshape(rows, cols)
                
                # Extract LSR by grouping pixels with similar orientations
                lsfim2, lsfarr = self.generate_regions(edge_img, lsr_thresh, lsfim2, lsfarr, dx, dy, rows, cols)
                # lsfim2, lsfarr = _lineSupport.generate_regions(edge_img, lsr_thresh, lsfim2, lsfarr, dx, dy, rows, cols)
        
        edge_img = np.zeros(rows*cols)	
                
        binidx = np.searchsorted([337.5, 360], data)

        edge_img[edgePixs[0][np.where(binidx == 1)[0]]] = 1
        
        binidx = np.searchsorted([0., 22.5], data)
                
        edge_img[edgePixs[0][np.where(binidx == 1)[0]]] = 1
        
        edge_img = edge_img.reshape(rows, cols)
        
        # Extract LSR by grouping pixels with similar orientations
        lsfim2, lsfarr = self.generate_regions(edge_img, lsr_thresh, lsfim2, lsfarr, dx, dy, rows, cols)
        # lsfim2, lsfarr = _lineSupport.generate_regions(edge_img, lsr_thresh, lsfim2, lsfarr, dx, dy, rows, cols)
        
        lsfarr = lsfarr[1:, :]	    # first row was a dummy
        
        if lsfarr.shape[0] > 0:
            
            for i in xrange(0, rows):

                for j in xrange(0, cols):
                        
                    lsfim1_1 = lsfim1[0, i, j]	    # max should equal lsfarr rows
                    lsfim2_1 = lsfim2[0, i, j]
                    
                    if lsfim1_1 > 0:
                        lsfim1_1 -= 1

                    if lsfim2_1 > 0:
                        lsfim2_1 -= 1
                        
                    if not lsfim1_1 and lsfim2_1:
                        continue

                    lsfim1_2 = lsfim1[1, i, j]	    # lengths
                    lsfim2_2 = lsfim2[1, i, j]
                        
                    if lsfim1_2 > lsfim2_2:
                        lsfarr[lsfim1_1, 5] += 1
                        lsfarr[lsfim2_1, 5] -= 1
                    else:
                        lsfarr[lsfim1_1, 5] -= 1
                        lsfarr[lsfim2_1, 5] += 1					
                        
            self.lsfarr = lsfarr[(lsfarr[:, 5] > 0)][:, :5]
            
            if len(self.lsfarr) == 0:
                self.lsfarr = np.zeros((1, 5))

        else:
            self.lsfarr = np.zeros((1, 5))
        
    def generate_regions(self, edge_img, lsr_thresh, lsfim, lsfarr, dx, dy, rows, cols):

        ori, num_objs = lab_img(edge_img)	    # boundaries labeled
        # bd = find_boundaries(edge_img)	# binary boundaries
        # bd = mark_boundaries(edge_img, bd)

        if lsfim.max() == 0:
            lsfima = np.zeros((rows, cols))
            lsfimb = np.zeros((rows, cols))
        else:
            lsfima = lsfim[0]
            lsfimb = lsfim[1]
        
        cnt = lsfarr.shape[0] - 1

        # TEST
        # ax = plt.figure().add_subplot(111)
        # ax.imshow(ori, interpolation='nearest')
        # TEST
        
        
        # loop through dimensions
        # for n in xrange(0, np.prod(bd.shape)):	# num_feas
        for n in xrange(1, num_objs):
        
            bidx = np.where(ori == n)

            try:
                y = bidx[0]
                x = bidx[1]
            except:
                continue
            
            # threshold for line length
            if len(x) <= lsr_thresh:
                continue

            # TEST
            # st = list(x).index(x.min())
            # ed = list(x).index(x.max())
            #
            # ax.plot((x[st], x[ed]), (y[st], y[ed]))
            # TEST
            
            
            a = fftshift(fft(x*y, len(x)))			
            a = np.divide(a, len(x))

            idx = np.floor(len(x) / 2) + 1

            lmx = a[idx].real
            lmy = a[idx].imag								

            a_idx_p = a[idx+1]
            a_idx_m = a[idx-1]

            llen = 2 * (np.abs(a[idx+1]) + np.abs(a[idx-1]))
            lorn = (np.arctan2(a[idx+1].imag, a[idx+1].real) + np.arctan2(a[idx-1].imag, a[idx-1].real)) / 2.

            # llen = abs(ne.evaluate('2. * (abs(a_idx_p) + abs(a_idx_m))'))
            # lorn = abs(ne.evaluate('(arctan2(a_idx_p.imag, a_idx_p.real) + arctan2(a_idx_m.imag, a_idx_m.real)) / 2.'))
            lcon = np.max(np.maximum(abs(dx[bidx]), abs(dy[bidx])))

            cnt += 1
            
            lsfima[bidx] = cnt
            lsfimb[bidx] = llen			
            
            # line features
            cl_list = [llen, lmx, lmy, lorn, lcon, 0]

            lsfarr_row = np.zeros(6)
            for cl in xrange(0, 6):
                lsfarr_row[cl] = cl_list[cl]
            
            lsfarr = np.vstack((lsfarr, lsfarr_row))

        lsfim[0] = lsfima
        lsfim[1] = lsfimb
        
        
        # TEST
        # plt.show()
        # sys.exit()
        # TEST
        
        
        return lsfim, lsfarr


def grad_mag(chBd):

    # normalize
    chBd = np.divide(np.subtract(chBd, chBd.mean()), chBd.std())
    
    # compute gradient orientation and magnitude
    edoim, edmim, dx, dy = img2_ori_edge(chBd)
    
    return edoim, edmim, dx, dy


def _feature_lsr(edge_img, mag_img, x_deriv, y_deriv):

    rows, cols = x_deriv.shape

    # threshold magnitude
    data, edge_pixs = getEdgePixs(edge_img, mag_img, .5)
    
    # quantize gradient orientations
    obj = binQ(data, edge_pixs, 5, x_deriv, y_deriv, rows, cols)   # any LSR below 5 pixels can be ignored
    
    lsfarr = obj.lsfarr
    
    bin_count = np.searchsorted(range(5, 200+4, 4), lsfarr[:, 0]).astype(np.float32)
    lenpmf = bin_count / bin_count.sum()
    
    bin_count = np.searchsorted(list(np.linspace(0, 10, num=np.floor(10./.5))), lsfarr[:,4]).astype(np.float32)
    
    contrastpmf = bin_count / bin_count.sum()
    
    fea1 = -(np.multiply(lenpmf, np.log(np.add(lenpmf, 1e-5))).sum())
    fea2 = lsfarr[:, 4].mean()
    fea3 = -(np.multiply(contrastpmf, np.log(np.add(lenpmf, 1e-5))).sum())
    
    feas = np.array([fea1, fea2, fea3])
    feas[(np.isnan(feas))] = 0.
    
    del edge_img, mag_img
    
    return feas