// Cloudflare Pages middleware — HTTP Basic Auth gate for the staging preview.
//
// The username/password are read from Pages environment variables
// PREVIEW_USER / PREVIEW_PASS, which you set in the Cloudflare dashboard
// (Pages project -> Settings -> Variables and secrets). Keeping them there,
// not in this file, means the password never lands in the public repo.
//
// This file lives only on the `draft` branch, so it never affects the live
// GitHub Pages site (served from `master`). If the variables aren't set yet,
// it fails closed and keeps the preview private.
export const onRequest = async ({ request, env, next }) => {
  const user = env.PREVIEW_USER;
  const pass = env.PREVIEW_PASS;
  const expected = user && pass ? "Basic " + btoa(`${user}:${pass}`) : null;

  const provided = request.headers.get("Authorization");
  if (!expected || provided !== expected) {
    return new Response("Authentication required.", {
      status: 401,
      headers: {
        "WWW-Authenticate": 'Basic realm="Preview", charset="UTF-8"',
        "Cache-Control": "no-store",
      },
    });
  }
  return next();
};
