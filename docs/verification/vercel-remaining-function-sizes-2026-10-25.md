# Remaining deployment function-size comparison

Verified 2026-10-25 through the live Vercel Resources view for nadhif-s1/thesis-project. The API lists 13 records: 11 Ready deployments and two Canceled records. All 11 Ready deployments in the user's screenshot were inspected; canceled records were not counted as successful bundle output. No deployments were modified or deleted during this audit.

Each table value is the sum of the displayed, rounded function sizes in BOM1. These sums rank deployment output size; they are not measured per-deployment billing attribution or guaranteed deletion savings. The last-30-days Usage page still displayed 9.19 GB during this inspection; this time-based historical total is distinct from the sum of the remaining Resources sizes.

| Deployment | Commit | Date (Jakarta) | Environment | Function count | Size each | Sum |
| --- | --- | --- | --- | ---: | ---: | ---: |
| [HnyVMwa7M](https://vercel.com/nadhif-s1/thesis-project/HnyVMwa7Mx7nVpvymd7uW9iujToc/resources) | a51ec95 | 2026-10-25 14:09 | production | 3 | 144 MB | 432 MB |
| [HeEQMiFq2](https://vercel.com/nadhif-s1/thesis-project/HeEQMiFq2D1TbybKyHYGtiMRSStJ/resources) | 3cfe5a5 | 2026-10-23 02:10 | production | 3 | 139 MB | 417 MB |
| [FiZzRk1vA](https://vercel.com/nadhif-s1/thesis-project/FiZzRk1vARdm62B41ry9ueEVdJLM/resources) | dbc6a2d | 2026-10-23 02:07 | production | 3 | 139 MB | 417 MB |
| [H9jLGP4gN](https://vercel.com/nadhif-s1/thesis-project/H9jLGP4gNgGajxwCjSddJb6sfGTW/resources) | e521d69 | 2026-10-25 14:40 | production | 3 | 137 MB | 411 MB |
| [9nbp3JPRL](https://vercel.com/nadhif-s1/thesis-project/9nbp3JPRLgVbfcuDushS8neNjXEX/resources) | a51ec95 | 2026-10-24 12:08 | production | 3 | 137 MB | 411 MB |
| [HvpytLeEY](https://vercel.com/nadhif-s1/thesis-project/HvpytLeEYzw4VXMevyZzRWS4pLUy/resources) | aa61d95 | 2026-10-24 12:06 | preview | 3 | 137 MB | 411 MB |
| [F37FU2hCi](https://vercel.com/nadhif-s1/thesis-project/F37FU2hCiefgxvRyuuL2ppfKM4fb/resources) | dd216ac | 2026-10-25 14:37 | preview | 3 | 136 MB | 408 MB |
| [SrpgR3bki](https://vercel.com/nadhif-s1/thesis-project/SrpgR3bki95iQPcPSA2cTRXj7Nje/resources) | 649b903 | 2026-10-18 22:03 | production | 3 | 98 MB | 294 MB |
| [EUrUHdiiB](https://vercel.com/nadhif-s1/thesis-project/EUrUHdiiBsqYJm5SS982JPf513ok/resources) | 98bad07 | 2026-10-18 21:51 | production | 3 | 98 MB | 294 MB |
| [GJq9Jsk8u](https://vercel.com/nadhif-s1/thesis-project/GJq9Jsk8uxc1m9H9gA8xVvpXymw8/resources) | 7427018 | 2026-10-20 23:17 | production | 3 | 85 MB | 255 MB |
| [EeoSZGLkL](https://vercel.com/nadhif-s1/thesis-project/EeoSZGLkLgwQfENFbNE9x5NUBT4i/resources) | 8efde87 | 2026-10-18 13:41 | production | 2 | 97.8 MB | 195.6 MB |

Total displayed Resources size: approximately **3,945.6 MB (3.95 GB)** across 32 functions. Ten deployments contain FastAPI plus the WhatsApp and admin queue subscribers. EeoSZGLkL has FastAPI and WhatsApp subscriber only. Every function in a given deployment displays the same size.

Largest: HnyVMwa7M, commit a51ec95, approximately 432 MB. Current production H9jLGP4gN is approximately 411 MB. Two production deployments share commit a51ec95 but display different sizes (432 and 411 MB), totaling approximately 843 MB; the commit SHA alone does not establish identical build output, and the cause of the size difference was not investigated. Resource size differences alone do not establish which deployment should be removed; preserve current production and required rollback releases.
