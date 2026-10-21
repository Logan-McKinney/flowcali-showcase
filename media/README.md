# Media

This folder holds the real recordings referenced by the main README. None are
committed yet; nothing here is a mock-up.

| File | What it is | Used for |
|---|---|---|
| `pike-original.mp4` | Original side-on pike push-up clip | Linked from README |
| `pike-overlay.mp4` | The same clip after FlowCali processing (skeleton + joint angles) | Linked from README |
| `pike-side-by-side.gif` | Short synchronized original + overlay loop | Hero image at the top of the README |
| `app-walkthrough.mp4` | iPhone screen recording, edited to 60–90 s | Linked from README |

GitHub plays `.mp4` files when you open them in the repo, but README files can
only embed images, so the hero needs to be a GIF (or an `.mp4` dragged into
the README editor on github.com, which hosts it as an attachment). Keep each
file under ~25 MB.

## Side-by-side clip

The overlay is rendered at the analysis frame rate (about 30 fps or lower) with
no audio, and it may have been trimmed in-app, so first check the two clips
start on the same frame. Find a clear event, such as the first moment the
elbows bend, in both and note the offset.

With [ffmpeg](https://ffmpeg.org/) (replace `0.00` with the offset in seconds
if the overlay starts later):

```sh
# 1. Side-by-side MP4, both scaled to the same height, constant 30 fps
ffmpeg -i pike-original.mp4 -ss 0.00 -i pike-overlay.mp4 \
  -filter_complex "[0:v]fps=30,scale=-2:720[a];[1:v]fps=30,scale=-2:720[b];[a][b]hstack" \
  -an -c:v libx264 -crf 23 -pix_fmt yuv420p side-by-side.mp4

# 2. A 4-6 second loop of one or two clean reps as a GIF (start time -ss, length -t)
ffmpeg -ss 2 -t 5 -i side-by-side.mp4 \
  -vf "fps=15,scale=900:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" \
  pike-side-by-side.gif
```

Aim for a GIF under ~8 MB; lower `fps` or `scale` if it's bigger. Labeling the
halves "Original" / "FlowCali overlay" (in any video editor, or with ffmpeg's
`drawtext`) helps people who skim.

## App walkthrough (60–90 s)

Suggested cut:

1. **0–10 s:** open the app, home screen.
2. **10–25 s:** choose a camera-roll video, trim, confirm the analysis.
3. **25–35 s:** the processing screen, sped up. Add an on-screen caption such as
   *"Processing sped up. Actual time ≈ 45 s on a local development backend."*
4. **35–85 s:** scroll the report at reading speed: score, overlay playback,
   what you did well, rep breakdown, what to fix, fatigue, prescription.

iMovie, CapCut or the Photos editor on iPhone are fine for trimming and speed
ramps. Don't cut the wait out without saying so; the caption is what keeps the
demo honest.

## Before committing any media — privacy check

- [ ] No email address, name, or account details visible (profile screen,
      sign-in screen, notifications, status bar).
- [ ] No other people, house numbers, mail, windows showing the street, or
      other identifying background details.
- [ ] No IP addresses, server URLs or developer menus visible (for example the
      Expo dev-client overlay).
- [ ] No notification banners from other apps.
- [ ] Location and other metadata removed (re-encoding with ffmpeg as above
      drops most of it; check with `ffprobe -show_format`).
- [ ] Only footage of yourself. Never footage of other athletes, or anything
      derived from it.
