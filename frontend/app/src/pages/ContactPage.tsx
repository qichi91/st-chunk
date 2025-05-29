import React from 'react';
import Typography from '@mui/material/Typography';
import Container from '@mui/material/Container';

const ContactPage: React.FC = () => {
    return (
        <Container sx={{ marginTop: 4 }}>
            <Typography variant="h4" component="h1" gutterBottom>
                Contact Us (TS)
            </Typography>
            <Typography variant="body1">
                Get in touch with us through this page, created with TypeScript.
            </Typography>
        </Container>
    );
}

export default ContactPage;