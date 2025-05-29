import React from 'react';
import Typography from '@mui/material/Typography';
import Container from '@mui/material/Container';

const AboutPage: React.FC = () => {
    return (
        <Container sx={{ marginTop: 4 }}>
            <Typography variant="h4" component="h1" gutterBottom>
                About Us (TS)
            </Typography>
            <Typography variant="body1">
                Learn more about our company and team here. This page uses TypeScript.
            </Typography>
        </Container>
    );
}

export default AboutPage;