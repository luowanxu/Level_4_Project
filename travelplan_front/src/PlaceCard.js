import React, { useState } from 'react';
import { 
  Card, 
  CardContent, 
  Box, 
  Typography, 
  Rating, 
  Chip,
  IconButton,
  Tooltip
} from '@mui/material';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import RestaurantIcon from '@mui/icons-material/Restaurant';
import HotelIcon from '@mui/icons-material/Hotel';
import AttractionsIcon from '@mui/icons-material/Attractions';
import PlaceIcon from '@mui/icons-material/Place';
import LocationOnIcon from '@mui/icons-material/LocationOn';
import LocalCafeIcon from '@mui/icons-material/LocalCafe';
import MuseumIcon from '@mui/icons-material/Museum';
import StorefrontIcon from '@mui/icons-material/Storefront';
import ParkIcon from '@mui/icons-material/Park';
import PlaceDetailDialog from './PlaceDetailDialog';

const PlaceCard = ({ place, type, onSelect, isSelected }) => {
  const [detailOpen, setDetailOpen] = useState(false);

  const getIconProps = () => {
    switch (type) {
      case 'restaurant':
        return {
          Icon: RestaurantIcon,
          color: '#FF9800',
          secondaryIcon: LocalCafeIcon
        };
      case 'attraction':
        return {
          Icon: AttractionsIcon,
          color: '#4CAF50',
          secondaryIcon: MuseumIcon
        };
      case 'hotel':
        return {
          Icon: HotelIcon,
          color: '#2196F3',
          secondaryIcon: StorefrontIcon
        };
      default:
        return {
          Icon: PlaceIcon,
          color: '#9C27B0',
          secondaryIcon: ParkIcon
        };
    }
  };

  const { Icon, color, secondaryIcon: SecondaryIcon } = getIconProps();

  const handleClick = (e) => {
    e.stopPropagation(); // 防止触发卡片的点击事件
    onSelect(place);
  };

  return (
    <>
      <Card 
       sx={{ 
         height: '100%', 
         display: 'flex', 
         flexDirection: 'column',
         cursor: 'pointer',
         position: 'relative',
         zIndex: 1, // 确保卡片的层级较低
         '&:hover': {
           boxShadow: 6,
           transform: 'scale(1.02)',
           transition: 'all 0.2s ease-in-out'
         }
       }}
        onClick={() => setDetailOpen(true)}
      >
        {/* 添加选择按钮 */}
        <IconButton
          onClick={handleClick}
          className="add-button"
          sx={{
            position: 'absolute',
            top: 8,
            right: 8,
            zIndex: 1,
            backgroundColor: 'white',
            '&:hover': {
              backgroundColor: 'rgba(255, 255, 255, 0.9)',
            }
          }}
        >
          <Tooltip title={isSelected ? "Remove from itinerary" : "Add to itinerary"}>
            {isSelected ? (
              <CheckCircleIcon sx={{ color: 'success.main' }} />
            ) : (
              <AddCircleOutlineIcon sx={{ color: color }} />
            )}
          </Tooltip>
        </IconButton>
        <Box
          sx={{
            height: 200,
            backgroundColor: `${color}15`,
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            position: 'relative',
            overflow: 'hidden'
          }}
        >
          <Icon sx={{ 
            fontSize: 80,
            color: color,
            opacity: 0.8
          }} />

          <SecondaryIcon sx={{
            position: 'absolute',
            fontSize: 120,
            color: color,
            opacity: 0.1,
            transform: 'rotate(-15deg)',
            right: -20,
            bottom: -20
          }} />
          <SecondaryIcon sx={{
            position: 'absolute',
            fontSize: 100,
            color: color,
            opacity: 0.1,
            transform: 'rotate(15deg)',
            left: -20,
            top: -20
          }} />

          <LocationOnIcon sx={{
            position: 'absolute',
            bottom: 8,
            right: 8,
            color: color,
            opacity: 0.6
          }} />
        </Box>

        <CardContent sx={{ flexGrow: 1 }}>
          <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
            <Typography variant="h6" component="div" sx={{ 
              wordBreak: 'break-word',
              color: color
            }}>
              {place.name}
            </Typography>
            <Icon sx={{ color: color }} />
          </Box>

          {place.rating && (
            <Box display="flex" alignItems="center" gap={1} mb={1}>
              <Rating 
                value={Number(place.rating)} 
                readOnly 
                precision={0.1}
                size="small"
              />
              <Typography variant="body2" color="text.secondary">
                ({place.user_ratings_total || 0})
              </Typography>
            </Box>
          )}

          {place.price_level && (
            <Typography variant="body2" color="text.secondary" mb={1}>
              Price: {'£'.repeat(place.price_level)}
            </Typography>
          )}

          {place.vicinity && (
            <Typography variant="body2" color="text.secondary" mb={1}>
              {place.vicinity}
            </Typography>
          )}

          {place.types && (
            <Box display="flex" gap={0.5} flexWrap="wrap" mb={1}>
              {place.types
                .filter(type => !['point_of_interest', 'establishment'].includes(type))
                .slice(0, 3)
                .map((type, index) => (
                  <Chip 
                    key={index} 
                    label={type.replace(/_/g, ' ').toLowerCase()} 
                    size="small"
                    sx={{ 
                      fontSize: '0.7rem',
                      textTransform: 'capitalize',
                      backgroundColor: `${color}15`,
                      color: color,
                      '& .MuiChip-label': {
                        color: 'inherit'
                      }
                    }}
                  />
                ))}
            </Box>
          )}

          {place.opening_hours && (
            <Typography 
              variant="body2" 
              color={place.opening_hours.open_now ? "success.main" : "error.main"}
              sx={{ mt: 1 }}
            >
              {place.opening_hours.open_now ? "Open Now" : "Closed"}
            </Typography>
          )}
        </CardContent>
      </Card>

      <PlaceDetailDialog
        open={detailOpen}
        onClose={() => setDetailOpen(false)}
        place={place}
        type={type}
      />
    </>
  );
};

export default PlaceCard;