// SelectedPlacesSidebar.js
import React from 'react';
import {
  Drawer,
  Box,
  Typography,
  IconButton,
  List,
  ListItem,
  ListItemText,
  Button,
  Divider,
  Rating,
  useTheme  // 添加这个
} from '@mui/material';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import { useNavigate } from 'react-router-dom';

const DRAWER_WIDTH = 350;

const SelectedPlacesSidebar = ({ 
  open, 
  onClose, 
  selectedPlaces, 
  onRemovePlace,
  onClearAll,
  zIndex,
  onProceed  // 添加这个参数
}) => {
  const theme = useTheme();

  return (
    <Drawer
      variant="persistent"
      anchor="left"
      open={open}
      sx={{
        width: DRAWER_WIDTH,
        flexShrink: 0,
        position: 'fixed',
        '& .MuiDrawer-paper': {
          width: DRAWER_WIDTH,
          boxSizing: 'border-box',
          position: 'fixed',
          height: '100%',
          zIndex: zIndex, // 使用传入的 zIndex
          boxShadow: theme.shadows[8], // 添加阴影效果
          bgcolor: 'background.paper', // 确保背景色不透明
        },
        // 确保所有子元素也保持在高层级
        '& .MuiList-root, & .MuiListItem-root, & .MuiTypography-root': {
          position: 'relative',
          zIndex: zIndex + 1
        },
        // 确保按钮和其他交互元素也在高层级
        '& .MuiButtonBase-root': {
          position: 'relative',
          zIndex: zIndex + 1
        },
        '& .MuiBackdrop-root': { // 如果有背景遮罩，也设置其z-index
          zIndex: zIndex - 1
        }
      }}
    >
      <Box sx={{ 
        display: 'flex', 
        alignItems: 'center', 
        p: 2,
        borderBottom: 1,
        borderColor: 'divider'
      }}>
        <Typography variant="h6" sx={{ flexGrow: 1 }}>
          Selected Places ({selectedPlaces.length})
        </Typography>
        <IconButton onClick={onClose}>
          {theme.direction === 'ltr' ? <ChevronLeftIcon /> : <ChevronRightIcon />}
        </IconButton>
      </Box>

      {selectedPlaces.length > 0 ? (
        <>
          <List sx={{ flexGrow: 1, overflow: 'auto' }}>
            {selectedPlaces.map((place, index) => (
              <React.Fragment key={place.place_id || index}>
                <ListItem
                  secondaryAction={
                    <IconButton 
                      edge="end" 
                      onClick={() => onRemovePlace(place)}
                      size="small"
                    >
                      <DeleteOutlineIcon />
                    </IconButton>
                  }
                  sx={{ pr: 7 }}
                >
                  <ListItemText
                    primary={place.name}
                    secondary={
                      <Box sx={{ mt: 0.5 }}>
                        {place.rating && (
                          <Box display="flex" alignItems="center" gap={1} mb={0.5}>
                            <Rating 
                              value={place.rating} 
                              readOnly 
                              size="small"
                              precision={0.1}
                            />
                            <Typography variant="body2" color="text.secondary">
                              ({place.user_ratings_total})
                            </Typography>
                          </Box>
                        )}
                        {place.vicinity && (
                          <Typography variant="body2" color="text.secondary">
                            {place.vicinity}
                          </Typography>
                        )}
                      </Box>
                    }
                  />
                </ListItem>
                {index < selectedPlaces.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>

          <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
            <Button
              variant="contained"
              fullWidth
              onClick={onProceed}  // 使用传入的 onProceed
              sx={{ mb: 1 }}
              disabled={selectedPlaces.length === 0}  // 如果没有选择任何地点则禁用
            >
              Proceed to Planning
            </Button>
            <Button
              variant="outlined"
              fullWidth
              color="error"
              onClick={onClearAll}
              disabled={selectedPlaces.length === 0}  // 如果没有选择任何地点则禁用
            >
              Clear All
            </Button>
          </Box>
        </>
      ) : (
        <Box sx={{ 
          p: 3, 
          display: 'flex', 
          flexDirection: 'column',
          alignItems: 'center',
          gap: 2 
        }}>
          <Typography color="text.secondary" align="center">
            No places selected yet.
            Select places from the list to create your itinerary.
          </Typography>
        </Box>
      )}
    </Drawer>
  );
};

export default SelectedPlacesSidebar;