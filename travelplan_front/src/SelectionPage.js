import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Container,
  Box,
  Typography,
  Tabs,
  Tab,
  Grid,
  Alert,
  IconButton,
  Button,
} from '@mui/material';
import RestaurantIcon from '@mui/icons-material/Restaurant';
import HotelIcon from '@mui/icons-material/Hotel';
import AttractionsIcon from '@mui/icons-material/Attractions';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import PlaceCard from './PlaceCard';

function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const SelectionPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { cityName, placesData } = location.state || {};
  const [tabValue, setTabValue] = useState(0);

  if (!cityName || !placesData) {
    return (
      <Container>
        <Box py={4}>
          <Alert 
            severity="error" 
            action={
              <Button color="inherit" size="small" onClick={() => navigate('/')}>
                Return to Search
              </Button>
            }
          >
            No city data found. Please start a new search.
          </Alert>
        </Box>
      </Container>
    );
  }

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const hasRestaurants = Array.isArray(placesData.restaurants) && placesData.restaurants.length > 0;
  const hasAttractions = Array.isArray(placesData.attractions) && placesData.attractions.length > 0;
  const hasHotels = Array.isArray(placesData.hotels) && placesData.hotels.length > 0;

  return (
    <Container maxWidth="lg">
      <Box sx={{ py: 4 }}>
        <Box display="flex" alignItems="center" mb={4}>
          <IconButton 
            onClick={() => navigate('/')}
            sx={{ mr: 2 }}
          >
            <ArrowBackIcon />
          </IconButton>
          <Box>
            <Typography variant="h4" component="h1">
              Explore {cityName}
            </Typography>
            <Typography variant="subtitle1" color="text.secondary">
              Discover places to eat, visit, and stay
            </Typography>
          </Box>
        </Box>

        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs 
            value={tabValue} 
            onChange={handleTabChange} 
            centered
            variant="fullWidth"
          >
            <Tab 
              icon={<RestaurantIcon />} 
              label={`Restaurants (${placesData.restaurants?.length || 0})`}
              disabled={!hasRestaurants}
            />
            <Tab 
              icon={<AttractionsIcon />} 
              label={`Attractions (${placesData.attractions?.length || 0})`}
              disabled={!hasAttractions}
            />
            <Tab 
              icon={<HotelIcon />} 
              label={`Hotels (${placesData.hotels?.length || 0})`}
              disabled={!hasHotels}
            />
          </Tabs>
        </Box>

        <TabPanel value={tabValue} index={0}>
          {hasRestaurants ? (
            <Grid container spacing={3}>
              {placesData.restaurants.map((place, index) => (
                <Grid item xs={12} sm={6} md={4} key={index}>
                  <PlaceCard place={place} type="restaurant" />
                </Grid>
              ))}
            </Grid>
          ) : (
            <Alert severity="info" sx={{ mt: 2 }}>
              No restaurant information available for this city.
            </Alert>
          )}
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          {hasAttractions ? (
            <Grid container spacing={3}>
              {placesData.attractions.map((place, index) => (
                <Grid item xs={12} sm={6} md={4} key={index}>
                  <PlaceCard place={place} type="attraction" />
                </Grid>
              ))}
            </Grid>
          ) : (
            <Alert severity="info" sx={{ mt: 2 }}>
              No attraction information available for this city.
            </Alert>
          )}
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          {hasHotels ? (
            <Grid container spacing={3}>
              {placesData.hotels.map((place, index) => (
                <Grid item xs={12} sm={6} md={4} key={index}>
                  <PlaceCard place={place} type="hotel" />
                </Grid>
              ))}
            </Grid>
          ) : (
            <Alert severity="info" sx={{ mt: 2 }}>
              No hotel information available for this city.
            </Alert>
          )}
        </TabPanel>
      </Box>
    </Container>
  );
};

export default SelectionPage;