import Button from '@mui/material/Button';
import { useAuth } from 'react-oidc-context';

function LoginButton() {
    const auth = useAuth();

    if (auth.isLoading) {
        return <Button color="inherit" disabled>Loading...</Button>;
    }

    if (!auth.isAuthenticated) {
        return (
            <Button color="inherit" onClick={() => auth.signinRedirect()}>
                Login
            </Button>
        );
    }

    // name
    console.log(auth.user?.profile.name);
    console.log(auth.user?.profile);
    return (
        <Button color="inherit" onClick={() => auth.signoutRedirect()}>
            Logout
        </Button>
    );
}

export default LoginButton;