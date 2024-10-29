import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  IconButton,
  Typography,
  Box,
  Rating,
  Chip,
  Divider,
  Grid,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import PhoneIcon from '@mui/icons-material/Phone';
import LanguageIcon from '@mui/icons-material/Language';
import LocationOnIcon from '@mui/icons-material/LocationOn';
import RestaurantIcon from '@mui/icons-material/Restaurant';
import HotelIcon from '@mui/icons-material/Hotel';
import AttractionsIcon from '@mui/icons-material/Attractions';

const PlaceDetailDialog = ({ open, onClose, place, type }) => {
  const getIconProps = () => {
    switch (type) {
      case 'restaurant':
        return {
          Icon: RestaurantIcon,
          color: '#FF9800',
        };
      case 'attraction':
        return {
          Icon: AttractionsIcon,
          color: '#4CAF50',
        };
      case 'hotel':
        return {
          Icon: HotelIcon,
          color: '#2196F3',
        };
      default:
        return {
          Icon: LocationOnIcon,
          color: '#9C27B0',
        };
    }
  };

  const { Icon, color } = getIconProps();

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      scroll="paper"
      PaperProps={{
        sx: {
          borderRadius: 2,
          backgroundImage: `linear-gradient(to bottom, ${color}15, white 200px)`,
        }
      }}
    >
      <DialogTitle sx={{ m: 0, p: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
        <Icon sx={{ color: color, fontSize: 32 }} />
        <Typography variant="h5" component="div" sx={{ flexGrow: 1, color }}>
          {place.name}
        </Typography>
        <IconButton
          onClick={onClose}
          sx={{
            position: 'absolute',
            right: 8,
            top: 8,
            color: (theme) => theme.palette.grey[500],
          }}
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>
      <DialogContent dividers>
        <Grid container spacing={3}>
          {/* 基本信息部分 */}
          <Grid item xs={12}>
            <Box display="flex" alignItems="center" gap={1} mb={2}>
              <Rating
                value={Number(place.rating) || 0}
                readOnly
                precision={0.1}
              />
              <Typography variant="body2" color="text.secondary">
                ({place.user_ratings_total || 0} reviews)
              </Typography>
            </Box>

            {/* 营业状态 */}
            {place.opening_hours && (
              <Box mb={2}>
                <Box display="flex" alignItems="center" gap={1}>
                  <AccessTimeIcon sx={{ color: 'text.secondary' }} />
                  <Typography
                    variant="body1"
                    color={place.opening_hours.open_now ? "success.main" : "error.main"}
                    fontWeight="bold"
                  >
                    {place.opening_hours.open_now ? "Open Now" : "Closed"}
                  </Typography>
                </Box>
              </Box>
            )}

            {/* 地址 */}
            {place.vicinity && (
              <Box display="flex" alignItems="flex-start" gap={1} mb={2}>
                <LocationOnIcon sx={{ color: 'text.secondary' }} />
                <Typography variant="body1">
                  {place.vicinity}
                </Typography>
              </Box>
            )}

            {/* 电话号码 */}
            {place.formatted_phone_number && (
              <Box display="flex" alignItems="center" gap={1} mb={2}>
                <PhoneIcon sx={{ color: 'text.secondary' }} />
                <Typography variant="body1">
                  {place.formatted_phone_number}
                </Typography>
              </Box>
            )}

            {/* 网站 */}
            {place.website && (
              <Box display="flex" alignItems="center" gap={1} mb={2}>
                <LanguageIcon sx={{ color: 'text.secondary' }} />
                <Typography
                  variant="body1"
                  component="a"
                  href={place.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  sx={{ color: 'primary.main', textDecoration: 'none' }}
                >
                  Visit Website
                </Typography>
              </Box>
            )}
          </Grid>

          {/* 分隔线 */}
          <Grid item xs={12}>
            <Divider />
          </Grid>

          {/* 类型和特征 */}
          {place.types && (
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Categories & Features
              </Typography>
              <Box display="flex" gap={1} flexWrap="wrap">
                {place.types
                  .filter(type => !['point_of_interest', 'establishment'].includes(type))
                  .map((type, index) => (
                    <Chip
                      key={index}
                      label={type.replace(/_/g, ' ').toLowerCase()}
                      sx={{
                        backgroundColor: `${color}15`,
                        color: color,
                      }}
                    />
                  ))}
              </Box>
            </Grid>
          )}

          {/* 价格等级 */}
          {place.price_level && (
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Price Level
              </Typography>
              <Typography variant="body1">
                {'£'.repeat(place.price_level)}
                <Typography component="span" color="text.secondary" ml={1}>
                  ({['Inexpensive', 'Moderate', 'Expensive', 'Very Expensive'][place.price_level - 1]})
                </Typography>
              </Typography>
            </Grid>
          )}
        </Grid>
      </DialogContent>
    </Dialog>
  );
};

export default PlaceDetailDialog;