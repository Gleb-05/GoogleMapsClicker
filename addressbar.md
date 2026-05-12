Using addressbar directly is explored to minimize gui-specific actions.
Using the google maps search bar and toggling between map and satellite view are both very gui-specific.
Moreover, when `gui_search.center_on_search_result` works, centering involves either the resource-heavy page reload, or hardcoded corrective map drag. Both of those can be omitted if the addressbar works.

Skipping through the boring stuff (found far below), it works.

# How it works

A choice:
- use decimal coordinates (preferrable), possible compatibility issues with degree-based software
- use degree coordinates (possible but undesirable), change map scale and type only with an additional link visit

## Decimal coordinates

In the current version of google maps, lefclicking in any part of the map brings up a context menu with decimal coordinates. Fortunately, the links also work on decimal coordinates. Which allows to do the following:
- Map: `www.google.com/maps/place//@{coords from leftclick here},17z`
- Sat: `www.google.com/maps/place//@{coords from leftclick here},542m/data=!3m2!1e3!4b1`

Manual testing shows that everything works!

## Degree coordinates

Simply visit this with relevant degree coordinates substituted:
- Base: `www.google.com/maps/place/48°06'00.0"N+2°06'00.0"E`

Only after the page that follows this link loads, can the map type and map scale be changed through parameters seen in ##Decimal_coordinates.

## About scale 

While working with Map, the zoom level of `17z` seems to be the default for all search results. Currently there is no need to alter it. On `17z`, all details significant to path planning are preserved. `18z` is blurry and too large without benefit, and `16z` was found to be missing on things like walking paths and other small details.

While working with Sat, the height from which the image was taken might vary between areas. But there is no need to change the default value of `542m`. The link will not raise an error on inaccurate height, the link will be fixed on the side of google to show the area from the nearest available height. Moreover, through random checking no severe height difference was found.

# The boring stuff

Omitting https://www.google.com/maps/ as the common part from links in two tables below.

<details>
<summary>Searching for `Laduree bretagne`</summary>

Condition | Link
| - | - |
Incognito, map | place/Ladur%C3%A9e+Bretagne/ <br>@48.8628084,2.3604114,17z/ <br>data=!3m1!4b1!4m6!3m5!1s0x47e66f6d7dfdb003:0xb4ce1a4c731e2f98!8m2!3d48.8628049!4d2.3629863!16s%2Fg%2F11ffltz899 <br>?entry=ttu&g_ep=EgoyMDI2MDUwNi4wIKXMDSoASAFQAw%3D%3D
Incognito, sat | place/Ladur%C3%A9e+Bretagne/ <br>@48.8628084,2.3604114,533m/ <br>data=!3m2!1e3!4b1!4m6!3m5!1s0x47e66f6d7dfdb003:0xb4ce1a4c731e2f98!8m2!3d48.8628049!4d2.3629863!16s%2Fg%2F11ffltz899 <br>?entry=ttu&g_ep=EgoyMDI2MDUwNi4wIKXMDSoASAFQAw%3D%3D
Default google account, map | place/Ladur%C3%A9e+Bretagne/ <br>@48.8628084,2.3604114,17z/ <br>data=!3m1!4b1!4m6!3m5!1s0x47e66f6d7dfdb003:0xb4ce1a4c731e2f98!8m2!3d48.8628049!4d2.3629863!16s%2Fg%2F11ffltz899 <br>?entry=ttu&g_ep=EgoyMDI2MDUwNi4wIKXMDSoASAFQAw%3D%3D
Default google account, sat | place/Ladur%C3%A9e+Bretagne/ <br>@48.8628084,2.3604114,533m/ <br>data=!3m2!1e3!4b1!4m6!3m5!1s0x47e66f6d7dfdb003:0xb4ce1a4c731e2f98!8m2!3d48.8628049!4d2.3629863!16s%2Fg%2F11ffltz899 <br>?entry=ttu&g_ep=EgoyMDI2MDUwNi4wIKXMDSoASAFQAw%3D%3D
Alt google account, map | place/Ladur%C3%A9e+Bretagne/ <br>@48.8628084,2.3604114,17z/ <br>data=!3m1!4b1!4m6!3m5!1s0x47e66f6d7dfdb003:0xb4ce1a4c731e2f98!8m2!3d48.8628049!4d2.3629863!16s%2Fg%2F11ffltz899 <br>?authuser=3&entry=ttu&g_ep=EgoyMDI2MDUwNi4wIKXMDSoASAFQAw%3D%3D
Alt google account, sat | place/Ladur%C3%A9e+Bretagne/ <br>@48.8628084,2.3604114,533m/ <br>data=!3m1!1e3!4m6!3m5!1s0x47e66f6d7dfdb003:0xb4ce1a4c731e2f98!8m2!3d48.8628049!4d2.3629863!16s%2Fg%2F11ffltz899 <br>?authuser=3&entry=ttu&g_ep=EgoyMDI2MDUwNi4wIKXMDSoASAFQAw%3D%3D

Things after `?` can be preserved from an initial query in case they are critical. It seems like they remain the same within successful and unsuccessful links. They don't seem to store identifiers. Here `authuser` helps choose between multiple authenticated google users, `entry=ttu` hints that the link was typed out rather than clicked, and `g_ep` most likely relates to google analytics. All those things can be dropped without harming the loading time or content of the webpage that follows the link.

Things relating to `data=` certainly store everything about a place, because if removed from the link, the webpage that follows stops displaying all place details, although still aligned with correct coordinates.

Codes between `!` after `data=` seem to relate to the parameters of the page. Some of them certainly determine what is shown - a map or a satellite image. Attempts to manipulate them to switch between a map and a satellite image were not successful.

Using addresses from the table above in the addressbar to visit pages directly.
 <br>
Condition | Link
| - | - |
Incognito, map | place/Ladur%C3%A9e+Bretagne/ <br>@48.8628049,2.3629863,17z/ <br>data=!3m1!4b1!4m6!3m5!1s0x47e66f6d7dfdb003:0xb4ce1a4c731e2f98!8m2!3d48.8628049!4d2.3629863!16s%2Fg%2F11ffltz899 <br>?entry=ttu&g_ep=EgoyMDI2MDUwNi4wIKXMDSoASAFQAw%3D%3D
Default google account, map | place/Ladur%C3%A9e+Bretagne/ <br>@48.8628049,2.3629863,17z/ <br>data=!3m1!4b1!4m6!3m5!1s0x47e66f6d7dfdb003:0xb4ce1a4c731e2f98!8m2!3d48.8628049!4d2.3629863!16s%2Fg%2F11ffltz899 <br>?entry=ttu&g_ep=EgoyMDI2MDUwNi4wIKXMDSoASAFQAw%3D%3D

Centering on the location works! See difference in coordinates.

</details>


<details>
<summary>Searching for `48,2`</summary>

Condition | Link
| - | - |
Incognito, map | /place/48%C2%B000'00.0%22N+2%C2%B000'00.0%22E/ <br>@48.0000036,1.9974251,17z/ <br>data=!3m1!4b1!4m4!3m3!8m2!3d48!4d2 <br>?entry=ttu&g_ep=EgoyMDI2MDUxMC4wIKXMDSoASAFQAw%3D%3D
Incognito, sat | /place/48%C2%B000'00.0%22N+2%C2%B000'00.0%22E/ <br>@48.0000036,1.9974251,542m/ <br>data=!3m2!1e3!4b1!4m4!3m3!8m2!3d48!4d2 <br>?entry=ttu&g_ep=EgoyMDI2MDUxMC4wIKXMDSoASAFQAw%3D%3D

The rules for switching between map and satellite are still not clear. 

The `data=` only stores the page parameters (an arbitrary coordinate has no place details).

Thins after `?` remain unchanged, hinting at the fact that they are session-related and solidifying that ignoring them will most likely work.

It is obvious that degrees after `/place/` cannot be fabricated easily. It seems working with decimal coordiates after the `@` sign is easier. This motivates the solution provided at the start of this .md document.

</details>