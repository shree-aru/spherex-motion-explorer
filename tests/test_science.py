"""Synthetic numerical fixtures used ONLY for unit tests, never displayed to users."""
import numpy as np
from PIL import Image
import io
from backend.science import robust_stretch, residual_regions, to_png, ScienceError


def test_shared_stretch_uses_both_epochs():
    a=np.array([[0., 2.], [3., np.nan]])
    b=np.array([[0., 20.], [1., np.nan]])
    lo, hi=robust_stretch(a,b)
    assert hi>3 and lo>=0
    a_png=Image.open(io.BytesIO(to_png(a,b,'a')))
    b_png=Image.open(io.BytesIO(to_png(a,b,'b')))
    assert a_png.size==(2,2) and b_png.mode=='RGBA'
    assert a_png.getpixel((1,0))[3]==0  # NaN in input bottom-right -> flipped to top-right


def test_difference_color_signs():
    a=np.array([[0.,20.],[10.,3.]])
    b=np.array([[30.,0.],[10.,3.]])
    im=np.asarray(Image.open(io.BytesIO(to_png(a,b,'difference'))))
    assert im.shape==(2,2,4)
    assert im[1,0,0]>im[1,0,2]  # B-A positive in input top-left, bottom after flip
    assert im[1,1,2]>im[1,1,0]  # B-A negative in input top-right


def test_residual_regions_are_review_cues_not_measurements():
    a=np.ones((8,8), dtype=float)
    b=a.copy(); b[3:5, 4:6] += 100
    regions=residual_regions(a,b)
    assert regions
    assert regions[0]['pixels'] == 4
    assert regions[0]['sign'] == 'B brighter'
    assert 'x_pixel' in regions[0] and 'y_pixel' in regions[0]
