import { UserManager, WebStorageStateStore } from 'oidc-client-ts';

export const userManager = new UserManager({
    authority: import.meta.env.VITE_AUTHORITY,
    // biome-ignore lint/style/useNamingConvention: Expected
    client_id: import.meta.env.VITE_CLIENT_ID,
    // biome-ignore lint/style/useNamingConvention: Expected
    // redirect_uri: `${window.location.origin}${window.location.pathname}`,
    redirect_uri: import.meta.env.VITE_REDIRECT_URI,
    // biome-ignore lint/style/useNamingConvention: Expected
    // post_logout_redirect_uri: window.location.origin,
    post_logout_redirect_uri: import.meta.env.VITE_POST_LOGOUT_REDIRECT_URI,
    userStore: new WebStorageStateStore({ store: window.localStorage }),
    monitorSession: true, // this allows cross tab login/logout detection
    scope: "openid profile email",
    response_type: "code",
});


export const onSigninCallback = () => {
    window.history.replaceState({}, document.title, window.location.pathname);
};
