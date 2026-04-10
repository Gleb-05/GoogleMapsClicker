
# History of development

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

