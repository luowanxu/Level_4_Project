import React from 'react';
import { TextField, Box, Typography, IconButton, Container } from '@mui/material';
import SearchIcon from '@mui/icons-material/Search'; // 引入搜索图标

const SearchPage = () => {
  return (
    <Container>
      <Box
        display="flex"
        flexDirection="column"
        justifyContent="center"
        alignItems="center"
        height="100vh"
      >
        <Typography variant="h3" gutterBottom>
          Where do you want to go?
        </Typography>
        <Box display="flex" justifyContent="center" alignItems="center">
          <TextField 
            id="search" 
            label="Search" 
            variant="outlined" 
            style={{ width: '300px' }}
          />
          <IconButton 
            aria-label="search" 
            style={{ marginLeft: '10px' }}
          >
            <SearchIcon />
          </IconButton>
        </Box>
      </Box>
    </Container>
  );
};

export default SearchPage;



