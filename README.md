# [BreadcrumbTrail](https://www.breadcrumbtrail.app/) is route-tracker for travelers and explorers

Starting as a way to keep tabs on a friend who is hiking the Pacific Crest Trail, I have expanded and opened BreadcrumbTrail to the public.

Built for those who wish to unplug from social platforms while off-the-grid hiking/camping/exploring, BreadcrumbTrail gives you an easy way to keep your family/friends up-to-date without having to break your wilderness immersion. All you need is to be able to send a text or email, and you can start leaving breadcrumbs.

This is the second website that I am proud to have brought online as I continue my journey to learn Python/WebDev and related programming languages. Please, feel free to send any advice/pull-requests my way, so I can continue to improve.

## When creating your free account, you will be provided a Map-ID and a Private-Key

The <b>Map-ID</b> is for sharing, and can be searched to display your Trails with no login needed. You can also hide, delete, and change which Trails you have active with ease.

The <b>Private-Key</b> is how you check in on your journey. You can text or email your Private-Key, your coordinates, and an optional message to check-in@breadcrumbtrail.app - and the Python-powered Back-End takes care of the rest. For those with Satellite Travel devices, such as the Garmin inReach (not sponsored), with a contact-checkin feature, simply add the check-in email to your contacts list.

## Step-by-Step

  * Create your account at https://www.breadcrumbtrail.app/signup
  * Click on your Map-ID (EXAMPLE#1234) at the top of the screen to view your Settings page, and take note of your Private-Key (EX#3456)
  * Create a Trail from your home screen by entering a trail name and clicking New Trail. This also sets the trail as active.
  * Send your Private-Key and your Latitude/Longitude to check-in@breadcrumbtrail.app OR use the check-in button online (feature in progress).
  * You may also attach a note (300 characters max) to your check-in by adding: <ul>message:"Your note here"</ul>
  * Check-ins are collected every 5 minutes. The time, date, and coordinates are parsed and ran through weather and altitude APIs
  * A marker is placed on your map with: check-in#, date/time, coordinates, elevation, weather, temperature, humidity, air quality, and note.
