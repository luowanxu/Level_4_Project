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
  useTheme
} from '@mui/material';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';

const DRAWER_WIDTH = 350;

const SelectedPlacesSidebar = ({ 
  open, 
  onClose, 
  selectedPlaces, 
  onRemovePlace,
  onClearAll,
  zIndex,
  onProceed
}) => {
  const theme = useTheme();

  return (
    <Drawer
      variant="persistent"
      anchor="left"
      open={open}
      sx={{
        width: open ? DRAWER_WIDTH : 0,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: DRAWER_WIDTH,
          boxSizing: 'border-box',
          position: 'fixed', // 改为 fixed 定位
          height: '100vh',
          border: 'none',
          borderRight: `1px solid ${theme.palette.divider}`,
          transition: theme.transitions.create(['transform'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.standard,
          }),
          transform: open ? 'none' : `translateX(-${DRAWER_WIDTH}px)`,
          overflowY: 'auto', // 确保侧边栏内容可以滚动
        },
      }}
    >
      {/* 侧边栏内容结构保持不变 */}
      <Box sx={{ 
        display: 'flex', 
        flexDirection: 'column',
        height: '100%', // 确保内容填满高度
      }}>
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

        <Box sx={{ 
          flexGrow: 1,
          overflowY: 'auto', // 使列表区域可滚动
        }}>
          {selectedPlaces.length > 0 ? (
            <List>
              {/* 列表项保持不变 */}
            </List>
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
        </Box>

        {selectedPlaces.length > 0 && (
          <Box sx={{ 
            p: 2, 
            borderTop: 1, 
            borderColor: 'divider',
            backgroundColor: 'background.paper', // 确保底部按钮区域有背景色
          }}>
            <Button
              variant="contained"
              className="proceed-button"
              fullWidth
              onClick={onProceed}
              sx={{ mb: 1 }}
            >
              Proceed to Planning
            </Button>
            <Button
              variant="outlined"
              fullWidth
              color="error"
              onClick={onClearAll}
            >
              Clear All
          </Button>
        </Box>
        )}
      </Box>
    </Drawer>
  );
};

export default SelectedPlacesSidebar;