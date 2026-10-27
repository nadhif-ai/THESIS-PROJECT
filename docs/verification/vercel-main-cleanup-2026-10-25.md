# Main production deployment cleanup

On 2026-10-25 the user authorized removing main deployments older than October 20. The cutoff was interpreted as 2026-10-20 00:00:00 Asia/Jakarta. Selection required both production target and Git branch main.

Vercel CLI removed nine matching deployments. A complete post-deletion listing confirmed no matching records remain, current production dpl_H9jLGP4gNgGajxwCjSddJb6sfGTW remains, and the three retained preview records remain. Production /health returned status ready, backend pinecone. The project has 13 deployment records remaining. Three older production deployments originating from dev or codex/single-knowledge-base were outside the main-branch scope and retained. Actual storage reduction has not been measured.

Deleted IDs:

- dpl_4RFAD6YAgdU9Qp4svUdpA1PRVm5m
- dpl_BRtKUFsvcYcfyqTR213CPqPqts3Y
- dpl_2WdwZKrnGCXaC7xtEKhHB6XtJTo6
- dpl_9Gak2oqkK8mgLme4UCXKQhyH6rQw
- dpl_6ry3X3yner78Z6dPwJSyVYXk8vNJ
- dpl_AAuVewCp3zNwHXb5DfmFcSBXWPwB
- dpl_EKoHVo66o5jcuAbQe2trCEhC97te
- dpl_5tAUUn2QPZxtimqiHxeWFiL61vqm
- dpl_ZgALAFSnVmM3xZCSdTE99x6DPngM
