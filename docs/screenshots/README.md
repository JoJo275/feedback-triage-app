# Screenshots

Three `.png` images referenced from the README, captured against the live
Railway deploy at <https://feedback-triage-app-production.up.railway.app>.

| File | What | How to capture |
| --- | --- | --- |
| `01-list.png` | List page with seeded data | Run `task seed` against production, visit `/`, full-page screenshot ~1280px wide. |
| `02-detail.png` | Detail / edit page mid-edit | Click any item, change one field, screenshot before saving. |
| `03-docs.png` | `/api/v1/docs` Swagger UI | Visit `/api/v1/docs`, screenshot the operations list expanded. |

Drop the image files into this directory and the README's table will pick
them up. Keep file size under ~300KB each (PNG-8 or `pngquant` is fine).

Until the screenshots exist this directory is intentionally empty
except for this README; do not commit placeholder images.
