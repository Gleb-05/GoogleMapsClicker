
# get_area_img development

## iter_drag... methods

See [images/displacements](images/displacements). An algorithm to traverse a rectangle region made of smaller rectangle areas is made. Traversal begins from the center of the rectangular region and should go through each area EXACTLY once. Traversal also has to end on the upper edge of the region.

The idea is to connect this algorithm to the gui automation to compose larger regions of the map from areas visible on the screen at one time.

## get_area_img

Return np array representing map region. Easy - compose area screenshots into one np array, guided by `iter_drag...`

## drag_area

Interact with gui during `iter_drag...` using this method.

See gradual elimination of issues.

```python
pyautogui.moveTo(x_from, y_from)
pyautogui.dragTo(x_to, y_to, 1)
time.sleep(0.1)
```
<img src="images/get_area_img/area_img_gliding.png" width="700">

Map gains inertia on dragTo that moves it after dragTo ends. Fix issue by introducing a short stop before releasing the mouse click.

```python
pyautogui.moveTo(x_from, y_from)
pyautogui.mouseDown()
time.sleep(0.1)
pyautogui.moveTo(x_to, y_to, 1)
time.sleep(0.1)
pyautogui.mouseUp()
time.sleep(0.1)
```
<img src="images/get_area_img/area_img_chunky.png" width="700">

Despite the absence of inertia, some displacement are present. See the body of water to the right of the center.

Run `get_area_img` multiple times, see high similarity of images. Suspect high precision - low accuracy of displacemenets.
Develop new `is_no_change` based on pixel difference to replace the old one based on ImageChops diff bbox, now called `strict_no_change`.
Check similar images with `strict_no_change`, see `False` that seems incorrect.
Check similar images with `is_no_change`, see avg pixel difference less than `0.01`.
Add empirical threshold of `0.05` to decide whether two images have no change between each other.

Develop `test_drag_shift` to make sure that displacements are stable. As seen here, they are.

<img src="images/get_area_img/test_drag_area.png">

Increase accuracy of `drag_area`: scale factor - no; corrective second drag - no

Final solution!
Relies on close examination of how google maps drag works. The drag begins when the mouse cursor travels 4 pixels with mouse down.

```python
# google maps pics up dragging on 4th pixel with mousedown !!!
pyautogui.moveTo(x_from - 3, y_from)
pyautogui.mouseDown()
time.sleep(0.1)
pyautogui.moveTo(x_from, y_from, 0.1)
pyautogui.moveTo(x_to, y_to, 0.3)
time.sleep(0.1)  # small stop needed to prevent inertia from moving areas further
pyautogui.mouseUp()
time.sleep(0.1)
```
<img src="images/get_area_img/area_img_correct.png" width="700">

In satellite view, each area loads in a different amount of time, sometimes longer that 0.1 sec, making a constant wait time unreliable. Add `wait_for_animation_end` to account for that.

```python
    """Replicate dragging the map by providing two sets of coordinates: where the dragging begins and where it ends."""
    # google maps pics up dragging on 4th pixel with mousedown !!!
    pyautogui.moveTo(x_from - 3, y_from)
    pyautogui.mouseDown()
    time.sleep(0.1)
    pyautogui.moveTo(x_from, y_from, 0.1)
    with wait_for_animation_end(region=None):
        pyautogui.moveTo(x_to, y_to, drag_duration)
        # time.sleep to prevent inertia from moving areas further - already accounted for
    pyautogui.mouseUp()
    time.sleep(0.1)
```

# Map projection

dd = decimal degrees

Google Maps uses Web Mercator projection:
- Sphere-to-cylinder conformal projection (preserve local angles and shapes)
- Straight meridians and parallels
- Distortion near the poles
- Poles are omitted (latitude is clamped before 90 deg)

Interpretation for rectangles of same pixel width and height (screenshots):
- latitude-longitude lines form a near-square projection grid
- Same pixel with covers same width in degrees everywhere
- Same pixel width covers less real distance near poles (projection distortion)
- Same pixel height covers less height in degrees near poles (projection distortion)
- Same degree height covers same real distance, but due to the previous point, \
  same pixel height covers less real distance near poles.

Corollaries:
- Larger regions require attention:
  - When estimating how many areas are in a region (r_width x r_height), the dd height of the center area is used. Since dd height of center area will be considerably smaller than dd height of areas at the bottom of the region, this may lead to overestimation. Even if r_height is overestimated by 1, it will lead to at least 2\*r_width unnecessary area scans, leading to detrimental processign time increase. A special scaling factor for area height that depend on latitude should be introduced to make r_height estimation more precise.
  - During path planning, there will be less meters per pixel near the poles. If only the pixel distance is taken into account, two paths with same pixel distance with one near the poles will be falsely evaluated as equivalent, although the one near the poles is better. A special factoring matrix should be introduced to account for the distortion, or the image itself must be rescaled.

The largest of the processed areas below shows the current scale - 0.2 deg (about 20km).

<img src="images/google_maps_pixel-meters.png" width="500">

At this scale all drawbacks of the projection can be ignored. Meters per pixel, as well as degrees per pixel, are almost linear, making the screenshots perfectly usable as-is for tasks of path planning.

## Proof for degrees on rectangles with same pixel dimensions:
- Area at (2.160845852872219, 50.05395239601597)
  -  area_width_dd=0.01291751878432379
  -  dwidth=0.0
  -  area_height_dd=0.0039886770449015785
  -  dheight=0.0
- Area at (2.160845852872219, 51.0212088046068)
  - area_width_dd=0.01291751878432379
  - dwidth=0.0
  - area_heigth_dd=0.003907713118174172
  - dheight=0.0

1 deg in latitude ~ 0.0001 deg change in deg-per-pixel


# Fix `get_dd_rect_img` overestimation of `r_width` and `r_height`

As established, imperfections of the map projection can be ignored. This invites use of constant `area_width_dd` and `area_height_dd` in `r_width` and `r_height` estimation. It's faster and easier than calling `get_area_dd_wh()` on each new region.

There is another reason to review things. The `area_dim_dd` (*dim used to mean either width or height for brevity*) from `get_area_dd_wh()` may lead to `r_dim` overestimation, as evidenced by the following. See the region in [images\r_dim_correct_estimation](./images/r_dim_correct_estimation) folder. It was constructed after the fix, with a grid that outlines individual areas for debug purposes. In the same folder, see two markers that correspond to left-up corner and right-down corner of the region, as set in `REGION_1` constant. Note that both markers appear within corresponding areas of the region, making it obvious that the fix was correct. Now note the [region..map](./map_regions/region_48.87295496938,1.88147722555_48.86096261907,1.911476845556_map_27.05.2026_18.26.46.png). See how it goes far beyond the markers specified by `REGION_1`, although they are captured very early in the region contruction. It means that before the fix, using `get_area_dd_wh()` on the central area of the region was not helpful in `r_dim` estimation.

Skipping a bunch of math (found below), 

## The conclusions

I would usually put this part in the end. But people like to see results, so here we are.

`area_width_dd` and `area_height_dd` constants make sence and there IS a way to find them.

Manually calling `get_area_dd_wh()` across the entire France gives a sence of the distribution of those values. The dd width differs on e-7 scale, while dd hight differences are on a e-4 scale. It means that `r_height` is more likely to be overestimated. Choosing between constant and dynamic `area_dim_dd` will not resolve this issue.

It might be possible to reverse-engineer the distortion and include it into `r_dim` estimation. But a more practical question is, how far can `area_dim_dd` values be pushed without distorting the `r_dim` values? The answer is, the larger the region, the smaller the interval that `area_dim_dd` can occupy while yielding the same estimated `r_dim`. Note that `area_width_dd` values occupy a large interval, while `area_height_dd` values occupy a much smaller interval with an almost constant lower bound.

## Data to support the conclusions

See `get_area_dd_wh()` sampled across the entire France:

```  
(0.01291751878432379 , 0.004099505502807688)
(0.012917457462526372, 0.004104199847375867)
(0.012917580106413418, 0.00410411952361045)
(0.012917620579149691, 0.004108811660152867)
(0.012917508666207667, 0.004085822071168366)
(0.012917578573356375, 0.004085472306080362)
(0.012917554351099980, 0.00423344401397685)
(0.0129176819017216,   0.004409910785682314)
(0.012917518784324233, 0.004154054820681097)
```

See bounds for `area_w_dd` and `area_h_dd` using `REGION_1` and `REGION_2`

```
area_w_bounds_1=(0.009999873335333328, 0.029999620005999983)
area_w_bounds_2=(0.011947242867661401, 0.013540208583349589)
area_h_bounds_1=(0.003997450103331819, 0.011992350309995459)
area_h_bounds_2=(0.004013117500747763, 0.004230042771058453)
```

See less strict bounds on distorted REGION_2 (was taken by hand)
```
area_w_bounds_2=(0.01291422, 0.01526226)
area_h_bounds_2=(0.00398613, 0.00422771)
```

## A bunch of math

Copying the `estimate_area_width_and_height_dd_constants_once()` docstring:

```python
"""
With initial `area_width_dd` and `area_height_dd` provided by `get_area_dd_wh()`, 
use `REGION_1` and `REGION_2` values to estimate `AREA_WIDTH_DD` and `AREA_HEIGHT_DD` constants. 
They shall satisfy the `(1 + 2*r_dim) * area_dim_dd >= region_dim_dd` inequality.

Steps:
- `estimate_r_dim()` is used to get the initial estimation of `r_dim`.
- `estimate_area_dim_dd_bounds()` is used to estimate bounds for the constants.
- Let `lower_1`, `upper_1`, `lower_2`, `upper_2` be chosen in a way that defines two nested intervals.
  A point that divides both intervals in equal proportion 
  will become the value of the relevant area_dim_dd constant.
"""
```

Copying the `estimate_r_dim(region_dim_dd, area_dim_dd)` docstring:

```python
"""
For either dim=width or dim=height, 
estimate minimal `r_dim` such that `(1 + 2*r_dim) * area_dim_dd >= region_dim_dd`.

Solution: `math.ceil((abs(region_dim_dd) - area_dim_dd) / (2*area_dim_dd))`.

This is an inverse of the `estimate_area_dim_dd_bounds` function.
"""
```

Now, the math.

Left-up and right-down corners that define each region allow to calculate `region_width_dd` and `region_height_dd` of the region.

The `(1 + 2*r_dim) * area_dim_dd >= region_dim_dd` inequality just establishes that regardless of how big the region is, it will be covered if enough areas are arranged in a grid. The inequality is left withour proof.

As can be seen, having `region_dim_dd` and `area_dim_dd` allows to estimate the `r_dim`. Conversely, having `region_dim_dd` and `r_dim` allows to estimate the `area_dim_dd`. This is exactly what `estimate_area_dim_dd_bounds(region_dim_dd, r_dim)` does, and here is how.

Remember that the solution is `math.ceil((abs(region_dim_dd) - area_dim_dd) / (2*area_dim_dd))`. Taking it to be equal to an arbitrary `x`, the solution may be rewritten as "`(abs(region_dim_dd) - area_dim_dd) / (2*area_dim_dd)` IS IN `(x-1, x]`". After trivial transformations, we get "`area_dim_dd` IS IN `[abs(region_dim_dd) / (3 + 2*x), abs(region_dim_dd) / (1 + 2*x)]`". Finally, by substituting `x` for `r_dim` values obtained from `estimate_r_dim`, we get concrete intervals for `area_width_dd` and `area_height_dd`. The substitution step makes the initial estimation of `r_dim` with actual GUI necessary, but it's enough to do it once.

Finally, by using two regions, two upper and two lower bounds are obtained for both `area_height_dd` and `area_width_dd`. As was aleady said, let the intervals be chosen in a way that defines two nested intervals, namely `[l1 l2 u2 u1]`. A point that divides both intervals in equal proportion will become the value of the relevant `area_dim_dd` constant. This choise as opposed to choosing a middle point comes from an intuition that on larger and larger regions the behavior with which the interval for `area_dim_dd` shrinks will not change.

Let the distance from the point to `u1` be `u`, and from the point to `l1` be `l`. Then, solving for `u + l = (u1-l1); u / l = (u - (u1-u2)) / (l - (l2-l1))` will provide a solution. The point will be at `u1 - (u1-l1)*(u1-u2) / (u1-u2 + l2-l1)`.

This concludes the cascade of functions that leads to `area_width_dd` and `area_height_dd` constants that will work almost anywhere in France.
