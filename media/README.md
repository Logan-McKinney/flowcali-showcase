# FlowCali demonstration media

These files are edited from the original recordings provided for the showcase. The exercise comparison and in-app walkthrough feature **different source clips**.

| File | Purpose |
| --- | --- |
| `pike-side-by-side.gif` | README hero: synchronized ~5-second original vs. skeleton overlay |
| `pike-original.mp4` | Re-encoded original exercise clip (without audio or original metadata) |
| `pike-overlay.mp4` | Re-encoded FlowCali skeleton-overlay clip |
| `pike-side-by-side.mp4` | Higher-quality MP4 version of the comparison (optional) |
| `app-walkthrough.mp4` | Edited iPhone demonstration (~71 seconds) |

## Walkthrough editing

The original screen capture was approximately 161 seconds. The edit keeps the app home screen, recording/selection interface, clip confirmation, distinct stages of background processing, and the analysis-report walkthrough (score, skeleton replay, corrections, fatigue and coaching). It removes the Profile screen showing an email, the camera-roll thumbnail grid, and much of the processing wait. The bottom of the phone display was cropped to remove the recurring RevenueCat development error notification. Audio was removed and the video re-encoded without source metadata.

The processing wait is explicitly labeled as shortened. In **this recording**, the elapsed interval from submission to results was roughly one minute. This is a single demonstration on a local development backend, not a measured average. Earlier demonstrations may have had different processing times.

The in-app video and the standalone pose-comparison clip have **different settings/subjects**, so they must not be presented as the exact same exercise input. The short comparison clips are frame-matched to one another.

## Before public release

**Confirm publication rights for both source recordings**. The standalone exercise clip appears to be distinct from the video selected inside the app. The in-app footage has an attribution watermark. Ensure you own or have express permission to republish the depicted athletes' footage; an app demonstration or social-media availability alone does not establish that right. If clearance is not available, replace the clips with your own consented footage, or blur/crop the in-app video and avoid including the standalone clip.

Also review the edited walkthrough for any remaining unwanted background details, identities, and on-screen information before pushing to a public repo. These edits are a first-pass privacy review, not a guarantee every detail is cleared.

No production source, third-party video datasets, configuration, or secrets are contained in this media folder.
