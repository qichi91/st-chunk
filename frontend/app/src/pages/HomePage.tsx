import React from 'react';
import Typography from '@mui/material/Typography';
import Container from '@mui/material/Container';

const HomePage: React.FC = () => {
    return (
        <Container sx={{ marginTop: 4 }}>
            <Typography variant="h4" component="h1" gutterBottom>
                Welcome to the Home Page! (TS)
            </Typography>
            <Typography variant="body1">
                This is the home page of our awesome application, built with TypeScript.
            </Typography>
        </Container>
    );
}

export default HomePage;