import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Autocomplete, 
  TextField, 
  Box, 
  Typography, 
  IconButton, 
  Container,
  CircularProgress,
  Alert
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';

const SearchPage = () => {
  const navigate = useNavigate();
  const [inputValue, setInputValue] = useState('');
  const [options, setOptions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [error, setError] = useState(null);
  const [selectedOption, setSelectedOption] = useState(null);

  const fetchCitySuggestions = async (searchText) => {
    if (!searchText || searchText.length < 2) {
      setOptions([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/search-city/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ searchText })
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch city suggestions');
      }
      
      const data = await response.json();
      
      if (data && data.data) {
        const cities = data.data.map(city => ({
          name: city.name,
          region: city.region || '',
          country: city.country || '',  // 添加国家信息
          label: `${city.name}${city.region ? `, ${city.region}` : ''}${city.country ? `, ${city.country}` : ''}`,
          wikiDataId: city.wikiDataId,
          type: city.type || 'CITY'  // 添加地点类型
        }));
        setOptions(cities);
        if (cities.length > 0) {
          setOpen(true);
        }
      }
    } catch (error) {
      console.error('Error fetching city suggestions:', error);
      setError('Failed to fetch city suggestions');
      setOptions([]);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (event, newInputValue) => {
    setInputValue(newInputValue);
    
    if (newInputValue.length >= 2) {
      setLoading(true);
      setOpen(true);
      const timeoutId = setTimeout(() => {
        fetchCitySuggestions(newInputValue);
      }, 300);
      return () => clearTimeout(timeoutId);
    } else {
      setOptions([]);
      setLoading(false);
      setOpen(false);
    }
  };

// SearchPage.js 中的相关部分

const handleOptionSelect = (event, value) => {
  if (value) {
    setSelectedOption(value);
    setInputValue(value.label);
  }
  setOpen(false);
};

const handleSearch = async () => {
  if (selectedOption) {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/city-places/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          cityName: selectedOption.name,
          region: selectedOption.region,    // 添加地区信息
          country: selectedOption.country,  // 添加国家信息
        })
      });

      if (!response.ok) {
        throw new Error('Failed to fetch city information');
      }

      const data = await response.json();
      navigate('/selection', { 
        state: { 
          cityName: selectedOption.name,
          region: selectedOption.region,    // 添加地区信息
          country: selectedOption.country,  // 添加国家信息
          placesData: data
        }
      });
    } catch (error) {
      console.error('Error fetching city data:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  } else {
    setError('Please select a location from the suggestions');
  }
};

  const handleKeyPress = (event) => {
    if (event.key === 'Enter') {
      handleSearch();
    }
  };

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
        {error && (
          <Alert severity="error" sx={{ mb: 2, width: '100%', maxWidth: '500px' }}>
            {error}
          </Alert>
        )}
        <Box 
          display="flex" 
          justifyContent="center" 
          alignItems="center"
        >
          <Autocomplete
            id="city-search"
            open={open}
            onOpen={() => {
              if (inputValue.length >= 2) {
                setOpen(true);
              }
            }}
            onClose={() => setOpen(false)}
            options={options}
            loading={loading}
            inputValue={inputValue}
            onChange={handleOptionSelect}
            onInputChange={handleInputChange}
            getOptionLabel={(option) => option.label || ''}
            style={{ width: 300 }}
            filterOptions={(x) => x}
            noOptionsText={inputValue.length >= 2 ? "No cities found" : "Type to search"}
            loadingText="Searching..."
            renderInput={(params) => (
              <TextField
                {...params}
                label="Search Places"
                variant="outlined"
                onKeyPress={handleKeyPress}
                InputProps={{
                  ...params.InputProps,
                  endAdornment: (
                    <React.Fragment>
                      {loading ? (
                        <CircularProgress color="inherit" size={20} />
                      ) : null}
                      {params.InputProps.endAdornment}
                    </React.Fragment>
                  ),
                }}
              />
            )}
          />
          <IconButton 
            aria-label="search" 
            style={{ marginLeft: '10px' }}
            onClick={handleSearch}
            disabled={loading || (!inputValue)}
          >
            <SearchIcon />
          </IconButton>
        </Box>
      </Box>
    </Container>
  );
};

export default SearchPage;