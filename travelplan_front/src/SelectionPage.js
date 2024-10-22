import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Container,
  Box,
  Typography,
  Tabs,
  Tab,
  Card,
  CardContent,
  CardMedia,
  Rating,
  Grid,
  Chip,
  Alert,
  IconButton,
  Button
} from '@mui/material';
import PlaceIcon from '@mui/icons-material/Place';
import RestaurantIcon from '@mui/icons-material/Restaurant';
import HotelIcon from '@mui/icons-material/Hotel';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';

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

const PlaceCard = ({ place, type }) => {
  const getIconByType = () => {
    switch (type) {
      case 'attraction': return <PlaceIcon />;
      case 'restaurant': return <RestaurantIcon />;
      case 'hotel': return <HotelIcon />;
      default: return <PlaceIcon />;
    }
  };

  return (
    <Card sx={{ 
      height: '100%', 
      display: 'flex', 
      flexDirection: 'column',
      '&:hover': {
        boxShadow: 6,
        transform: 'scale(1.02)',
        transition: 'all 0.2s ease-in-out'
      }
    }}>
      <CardMedia
        component="img"
        height="200"
        image={place.photo?.images?.original?.url || `/api/placeholder/400/200`}
        alt={place.name}
        sx={{ objectFit: 'cover' }}
      />
      <CardContent sx={{ flexGrow: 1 }}>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
          <Typography variant="h6" component="div">
            {place.name}
          </Typography>
          {getIconByType()}
        </Box>

        {place.rating && (
          <Box display="flex" alignItems="center" gap={1} mb={1}>
            <Rating 
              value={Number(place.rating)} 
              readOnly 
              precision={0.5}
              size="small"
            />
            <Typography variant="body2" color="text.secondary">
              ({place.num_reviews || 0} reviews)
            </Typography>
          </Box>
        )}

        {place.price_level && (
          <Typography variant="body2" color="text.secondary" mb={1}>
            Price: {'£'.repeat(place.price_level)}
          </Typography>
        )}

        {place.address && (
          <Typography variant="body2" color="text.secondary" mb={1}>
            {place.address}
          </Typography>
        )}

        {place.cuisine && (
          <Box display="flex" gap={0.5} flexWrap="wrap" mb={1}>
            {place.cuisine.slice(0, 3).map((cuisine, index) => (
              <Chip 
                key={index} 
                label={cuisine.name} 
                size="small"
                sx={{ fontSize: '0.7rem' }}
              />
            ))}
          </Box>
        )}

        {place.description && (
          <Typography variant="body2" color="text.secondary" mb={1}>
            {place.description.slice(0, 150)}
            {place.description.length > 150 ? '...' : ''}
          </Typography>
        )}

        {place.website && (
          <Button 
            variant="contained" 
            fullWidth 
            size="small"
            sx={{ mt: 'auto' }}
            onClick={() => window.open(place.website, '_blank')}
          >
            Visit Website
          </Button>
        )}
      </CardContent>
    </Card>
  );
};

const SelectionPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { cityName, placesData } = location.state || {};
  const [tabValue, setTabValue] = useState(0);

  // 检查是否有有效数据
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

  // 检查每个类别是否有数据
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
              icon={<PlaceIcon />} 
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