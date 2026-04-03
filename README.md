The task is to get satellite imagery for path planning. Ideally, altitude and transit data should also be obtained.

The most obvious solution - **Google Maps**.
Using its API requires a setup with a credit card. Additionally, there is a limit on how many API calls can be made with a Free tier account, and the amount appears to be rather restricting. However, the Google Maps API provides a wide range of data in a clear and structured format, enabling data extraction within seconds. Compared to other options, it still may be worthwhile to perform a one-time comprehensive data extraction.

Extracting information from Google Maps without API is still possible through automation of GUI (graphical user interface).
GUI Automation is linked to its own challenges, amongst which:
- fragile setup: the interface changes on different screens, turning many variables inaccurate.
- uncertainty in variable usage: variables introduced for one context are often reused elsewhere, but as the codebase expands, developers may create redundant variables due to limited awareness of existing ones.
- unreliable behavior: sometimes correct code doesn't work on first try, only after two or more repeated executions the code resumes working as expected.
- abundance of failsafes: the logic for "waiting for page updates" or "repeating some actions" should be applied to all new code, which makes the development of new functionality difficult.
- graphical data: while other tools allow to download relevant data as a collection of points or values, GUI automation can only produce screenshots.

Ignoring the downsides, GUI automation allows to extract high-quality graphical data at the expence of time. One computer can be left to work continuously for a week, but yield terrain and transit data for a large area from Google Maps as a result.

Notice that terrain and transit data may not be enough to arrive at optimal path planning. **See (48.643650, 1.921213) as an example**. The terrain by itself fails to capture the presence of a river that cannot be crossed. The bottom right area relative to the point doesn't appear to have roads. And transit data reinforces this evaluation of the area.

Using *historical satellite imagery* should be useful, allowing to infer where the roads are based on the regions of stability. Consider the following five images, with the last one being from Google Maps:

| Year | Image |
| ---: | ----- |
| 2003 | <img src="images/google_earth_2003.png" width="700"> |
| 2010 | <img src="images/google_earth_2010.png" width="700"> |
| 2016 | <img src="images/google_earth_2016.png" width="700"> |
| 2024 | <img src="images/google_earth_2024.png" width="700"> |
| 2024 | <img src="images/google_maps_2024.png" width="700">  |

The bottom right area clearly has roads that were neither marked nor visible on Google Maps. Additionally, in earlier years the division of the area into rectangles is much more apparent.

The task of downloading historical satellite imagery seems to be common (https://gis.stackexchange.com/questions/340605/mass-downloading-google-earth-historical-imagery). Apart from Google Earth, [Landsat](https://developers.google.com/earth-engine/datasets/catalog/landsat) and [Sentinel](https://developers.google.com/earth-engine/datasets/catalog/sentinel) are suggested.

If existing solutions fail, this repository may be extended to work with Google Earth via GUI automation. However, due to its significant limitations, other methods of obtaining the relevant data should be prioritized.

Moving away from solutions provided by Google:
- https://www.openstreetbrowser.org/
- https://www.openstreetmap.org/
- https://www.geoportail.gouv.fr/

Those solutions provide the same kinds of data, but they are open-sourced.