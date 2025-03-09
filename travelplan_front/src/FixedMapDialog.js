// FixedMapDialog.js
import React, { useState, useMemo, useEffect, useRef } from 'react';
import { 
  Dialog, 
  DialogContent, 
  IconButton, 
  Typography, 
  Box,
  Chip,
  AppBar,
  Toolbar,
  Tabs,
  Tab,
  useTheme,
  useMediaQuery,
  CircularProgress,
  Paper,
  Button,
  Divider
} from '@mui/material';
import { Close, ViewList, Map as MapIcon } from '@mui/icons-material';

const FixedMapDialog = ({ open, handleClose, events, eventsByDay }) => {
  const [currentDay, setCurrentDay] = useState(0);
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('md'));
  const [loading, setLoading] = useState(false);
  const [viewMode, setViewMode] = useState('map'); // 'map' or 'list'
  const [selectedPlace, setSelectedPlace] = useState(null);
  const iframeRef = useRef(null);

  // 处理日期切换
  const handleDayChange = (event, newValue) => {
    setCurrentDay(newValue);
    setSelectedPlace(null);
  };

  // 计算此日期有多少地点
  const getPlaceCount = (day) => {
    return (eventsByDay[day] || []).filter(event => 
      event.type !== 'transit' && hasValidCoordinates(event)
    ).length;
  };

  // 检查事件是否有有效坐标
  const hasValidCoordinates = (event) => {
    return event.place?.geometry?.location?.lat && event.place?.geometry?.location?.lng;
  };

  // 过滤当前日期的地点事件（仅包含有有效坐标的地点）
  const placeEvents = useMemo(() => {
    if (!events) return [];
    const currentDayEvents = events.filter(event => Number(event.day) === currentDay);
    return currentDayEvents.filter(event => 
      event.type !== 'transit' && hasValidCoordinates(event)
    );
  }, [events, currentDay]);

  // 处理地点选择
  const handlePlaceSelect = (event) => {
    setSelectedPlace(event);
    
    // 向iframe发送消息，高亮选中的标记
    if (iframeRef.current && hasValidCoordinates(event)) {
      const message = {
        type: 'selectMarker',
        placeId: event.id,
        lat: event.place.geometry.location.lat,
        lng: event.place.geometry.location.lng
      };
      
      try {
        iframeRef.current.contentWindow.postMessage(message, '*');
      } catch (error) {
        console.error('Failed to send message to iframe:', error);
      }
    }
  };

  // 计算地图的边界和中心点
  const mapBounds = useMemo(() => {
    if (placeEvents.length === 0) return null;
    
    // 计算包含所有地点的边界
    let minLat = Infinity, maxLat = -Infinity, minLng = Infinity, maxLng = -Infinity;
    
    placeEvents.forEach(event => {
      const { lat, lng } = event.place.geometry.location;
      minLat = Math.min(minLat, lat);
      maxLat = Math.max(maxLat, lat);
      minLng = Math.min(minLng, lng);
      maxLng = Math.max(maxLng, lng);
    });
    
    // 增加边界外边距
    const latMargin = (maxLat - minLat) * 0.1 || 0.01;
    const lngMargin = (maxLng - minLng) * 0.1 || 0.01;
    
    return {
      minLat: minLat - latMargin,
      maxLat: maxLat + latMargin,
      minLng: minLng - lngMargin,
      maxLng: maxLng + lngMargin
    };
  }, [placeEvents]);

  // 创建地图HTML内容，使用正确的OpenStreetMap标记
  const createMapHtml = useMemo(() => {
    if (!mapBounds || placeEvents.length === 0) return '';
    
    const { minLat, maxLat, minLng, maxLng } = mapBounds;
    
    // 生成所有地点的标记数据
    const markersData = placeEvents.map((event, index) => {
      const { lat, lng } = event.place.geometry.location;
      return {
        id: event.id,
        title: event.title,
        lat,
        lng,
        label: index + 1
      };
    });
    
    // 创建完整的地图HTML，使用Leaflet
    return `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8">
        <title>Trip Map</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
        <style>
          body, html, #map {
            width: 100%;
            height: 100%;
            margin: 0;
            padding: 0;
          }
          .custom-marker {
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            font-weight: bold;
            color: white;
            border: 2px solid white;
            box-shadow: 0 0 4px rgba(0,0,0,0.5);
          }
          .marker-default {
            background-color: #1976d2;
            width: 24px;
            height: 24px;
            font-size: 12px;
          }
          .marker-selected {
            background-color: #f44336;
            width: 32px;
            height: 32px;
            font-size: 16px;
            z-index: 1000 !important;
          }
        </style>
      </head>
      <body>
        <div id="map"></div>
        <script>
          // 初始化地图
          const map = L.map('map').fitBounds([
            [${minLat}, ${minLng}],
            [${maxLat}, ${maxLng}]
          ]);
          
          // 添加地图图层
          L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          }).addTo(map);
          
          // 标记点数据
          const markers = ${JSON.stringify(markersData)};
          const markerElements = {};
          
          // 创建自定义标记点图标
          function createCustomIcon(label, isSelected) {
            const className = isSelected ? 'custom-marker marker-selected' : 'custom-marker marker-default';
            
            return L.divIcon({
              className: '',
              html: '<div class="' + className + '">' + label + '</div>',
              iconSize: isSelected ? [32, 32] : [24, 24],
              iconAnchor: isSelected ? [16, 16] : [12, 12]
            });
          }
          
          // 添加所有标记点
          markers.forEach(marker => {
            const icon = createCustomIcon(marker.label, false);
            const leafletMarker = L.marker([marker.lat, marker.lng], { icon }).addTo(map);
            
            leafletMarker.bindTooltip(marker.title);
            markerElements[marker.id] = {
              marker: leafletMarker,
              data: marker
            };
          });
          
          // 处理选择标记事件
          window.addEventListener('message', function(event) {
            if (event.data && event.data.type === 'selectMarker') {
              // 重置所有标记为默认样式
              Object.values(markerElements).forEach(m => {
                m.marker.setIcon(createCustomIcon(m.data.label, false));
              });
              
              // 设置选中的标记为高亮样式
              if (markerElements[event.data.placeId]) {
                const selectedMarker = markerElements[event.data.placeId];
                selectedMarker.marker.setIcon(createCustomIcon(selectedMarker.data.label, true));
                
                // 可选：平滑移动到选中的标记
                // map.panTo([event.data.lat, event.data.lng], { animate: true });
              }
            }
          });
        </script>
      </body>
      </html>
    `;
  }, [mapBounds, placeEvents]);

  // 渲染地图视图
  const renderMap = () => {
    if (placeEvents.length === 0) {
      return (
        <Box sx={{ 
          height: '400px', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          backgroundColor: '#f5f5f5' 
        }}>
          <Typography variant="body1">No places with valid coordinates found for this day</Typography>
        </Box>
      );
    }
    
    return (
      <Box sx={{ height: '400px', width: '100%', position: 'relative' }}>
        <iframe 
          ref={iframeRef}
          srcDoc={createMapHtml}
          width="100%" 
          height="100%" 
          frameBorder="0" 
          style={{ border: '1px solid #ccc' }}
          allowFullScreen
          aria-hidden="false"
          title="Interactive Map"
        />
      </Box>
    );
  };

  // 渲染列表视图
  const renderList = () => {
    if (placeEvents.length === 0) {
      return (
        <Box sx={{ p: 3, textAlign: 'center' }}>
          <Typography variant="body1">No places with valid coordinates scheduled for this day</Typography>
        </Box>
      );
    }
    
    return (
      <Box sx={{ p: 2 }}>
        {placeEvents.map((event, index) => (
          <Paper
            key={event.id}
            elevation={selectedPlace?.id === event.id ? 3 : 1}
            sx={{
              mb: 2,
              p: 2,
              borderLeft: '4px solid',
              borderColor: selectedPlace?.id === event.id ? 'primary.main' : 'divider',
              cursor: 'pointer',
              '&:hover': {
                backgroundColor: 'rgba(0, 0, 0, 0.04)'
              }
            }}
            onClick={() => handlePlaceSelect(event)}
          >
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                {index + 1}. {event.title}
              </Typography>
              {event.place?.rating && (
                <Chip 
                  size="small"
                  label={`${event.place.rating} ★`}
                  color="primary"
                  variant="outlined"
                />
              )}
            </Box>
            
            {event.startTime && event.endTime && (
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                {event.startTime} - {event.endTime}
              </Typography>
            )}
            
            {event.place?.vicinity && (
              <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                {event.place.vicinity}
              </Typography>
            )}
          </Paper>
        ))}
      </Box>
    );
  };

  // 当前日期所有事件（包括没有坐标的地点事件和交通事件）
  const allCurrentDayEvents = useMemo(() => {
    if (!events) return [];
    return events.filter(event => Number(event.day) === currentDay);
  }, [events, currentDay]);

  // 渲染底部的事件索引条
  const renderEventStrip = () => {
    // 过滤出所有非交通事件
    const nonTransitEvents = allCurrentDayEvents.filter(event => event.type !== 'transit');
    
    if (nonTransitEvents.length === 0) {
      return (
        <Box sx={{ p: 2, textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary">No events for this day</Typography>
        </Box>
      );
    }
    
    return (
      <Box sx={{ display: 'flex', p: 1, overflowX: 'auto' }}>
        {nonTransitEvents.map((event, index) => {
          // 检查是否有有效坐标
          const hasCoordinates = hasValidCoordinates(event);
          // 找出在placeEvents中的索引（如果有）
          const placeIndex = placeEvents.findIndex(p => p.id === event.id);
          
          return (
            <Paper
              key={event.id}
              elevation={selectedPlace?.id === event.id ? 3 : 1}
              sx={{
                p: 1,
                mr: 1,
                minWidth: '200px',
                cursor: hasCoordinates ? 'pointer' : 'default',
                borderTop: '3px solid',
                borderColor: selectedPlace?.id === event.id ? 'primary.main' : 
                  hasCoordinates ? 'divider' : 'error.light',
                opacity: hasCoordinates ? 1 : 0.7,
              }}
              onClick={() => hasCoordinates && handlePlaceSelect(event)}
            >
              <Typography variant="subtitle2">
                {hasCoordinates ? (placeIndex + 1) + '. ' : '(No location) '}
                {event.title}
              </Typography>
              {event.startTime && (
                <Typography variant="caption" display="block" color="text.secondary">
                  {event.startTime}
                </Typography>
              )}
              {!hasCoordinates && (
                <Typography variant="caption" display="block" color="error.main">
                  No coordinates available
                </Typography>
              )}
            </Paper>
          );
        })}
      </Box>
    );
  };

  return (
    <Dialog 
      fullScreen={fullScreen}
      maxWidth="md" 
      fullWidth 
      open={open} 
      onClose={handleClose}
      aria-labelledby="map-dialog-title"
    >
      <AppBar position="static" color="primary">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Trip Map
          </Typography>
          <Button 
            color="inherit" 
            startIcon={viewMode === 'map' ? <ViewList /> : <MapIcon />}
            onClick={() => setViewMode(viewMode === 'map' ? 'list' : 'map')}
          >
            {viewMode === 'map' ? 'List View' : 'Map View'}
          </Button>
          <IconButton
            edge="end"
            color="inherit"
            onClick={handleClose}
            aria-label="close"
          >
            <Close />
          </IconButton>
        </Toolbar>
      </AppBar>
      
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs 
          value={currentDay} 
          onChange={handleDayChange} 
          variant="scrollable"
          scrollButtons="auto"
        >
          {Object.keys(eventsByDay || {}).map((day) => (
            <Tab 
              key={day} 
              label={`Day ${Number(day) + 1}`} 
              icon={
                <Chip 
                  size="small" 
                  label={`${getPlaceCount(day)} places`} 
                  color="primary" 
                  variant="outlined"
                />
              }
              iconPosition="end"
            />
          ))}
        </Tabs>
      </Box>
      
      <DialogContent sx={{ p: 0 }}>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
            <CircularProgress />
            <Typography sx={{ ml: 2 }}>Loading...</Typography>
          </Box>
        ) : (
          <Box>
            {viewMode === 'map' ? (
              // 地图视图
              <Box>
                {renderMap()}
                <Divider />
                <Box sx={{ maxHeight: '200px', overflow: 'auto' }}>
                  {renderEventStrip()}
                </Box>
              </Box>
            ) : (
              // 列表视图
              renderList()
            )}
          </Box>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default FixedMapDialog;