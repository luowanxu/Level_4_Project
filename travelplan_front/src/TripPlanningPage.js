import React, { useState, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Container,
  Box,
  Typography,
  IconButton,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  ToggleButtonGroup,  // 只需要导入一次
  ToggleButton,       // 只需要导入一次
  Fade
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers';
import {
  ArrowBack,
  Edit,
  DirectionsWalk,
  DirectionsCar,
  DirectionsTransit,
  EditCalendar as EditIcon,
  Preview as PreviewIcon
} from '@mui/icons-material';
import TimelineView from './TimelineView';
import TimelinePreview from './TimelinePreview';

const TripPlanningPage = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const { selectedPlaces, previousPageData } = location.state || { selectedPlaces: [] };
    const [events, setEvents] = useState([]);
    const [viewMode, setViewMode] = useState('edit');
    

  // 状态管理
  const [tripName, setTripName] = useState('My Trip');
  const [peopleCount, setPeopleCount] = useState(1);
  const [startDate, setStartDate] = useState(null);
  const [endDate, setEndDate] = useState(null);
  const [transportMode, setTransportMode] = useState('walking');
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);

  // 编辑对话框临时状态
  const [editValues, setEditValues] = useState({
    tripName,
    peopleCount,
    startDate,
    endDate,
    transportMode,
  });


  const handleEventsUpdate = useCallback((newEvents) => {
    setEvents(newEvents);
  }, []);

  // 处理对话框打开
  const handleEditClick = () => {
    setEditValues({
      tripName,
      peopleCount,
      startDate,
      endDate,
      transportMode,
    });
    setIsEditDialogOpen(true);
  };

  // 处理对话框保存
  const handleSave = () => {
    setTripName(editValues.tripName);
    setPeopleCount(editValues.peopleCount);
    // 确保日期是 Date 对象
    setStartDate(editValues.startDate ? new Date(editValues.startDate) : null);
    setEndDate(editValues.endDate ? new Date(editValues.endDate) : null);
    setTransportMode(editValues.transportMode);
    setIsEditDialogOpen(false);
  };

  // 格式化日期范围显示
  const getDateRangeText = () => {
    if (!startDate || !endDate) return 'Dates not set';
    return `${startDate.toLocaleDateString()} - ${endDate.toLocaleDateString()}`;
  };

  // 获取交通方式显示文本
  const getTransportText = () => {
    const modes = {
      walking: 'Walking',
      transit: 'Public Transit',
      driving: 'Driving',
    };
    return modes[transportMode] || '';
  };

  return (
    <Container maxWidth={false} sx={{ px: 3 }}> {/* 改为 false 以使用更多空间 */}
      <Box sx={{ py: 4 }}>
        {/* 头部区域 */}
        <Box display="flex" alignItems="flex-start" mb={4}>
          <IconButton 
            onClick={() => navigate(-1)} // 修改这里，使用 navigate(-1)
            sx={{ mr: 2 }}
          >
            <ArrowBack />
          </IconButton>
          
          <Box sx={{ flexGrow: 1 }}>
            <Box display="flex" alignItems="center" mb={1}>
              <Typography variant="h4" component="h1" sx={{ flexGrow: 1 }}>
                {tripName}
              </Typography>
              <IconButton onClick={handleEditClick} size="small">
                <Edit />
              </IconButton>
            </Box>
            
            <Typography variant="subtitle1" color="text.secondary" gutterBottom>
              {peopleCount} {peopleCount === 1 ? 'person' : 'people'} • {getTransportText()}
            </Typography>
            <Typography 
              variant="subtitle1" 
              color="text.secondary" 
              sx={{ 
                mt: 0.5,
                fontSize: '0.9rem',  // 稍微小一点的字体
                opacity: 0.9        // 稍微淡一点的颜色
              }}
            >
              {getDateRangeText()}
            </Typography>
          </Box>
        </Box>

        <Box sx={{ 
          display: 'flex', 
          justifyContent: 'center',
          mb: 3 
        }}>
          <ToggleButtonGroup
            value={viewMode}
            exclusive
            onChange={(e, newMode) => {
              if (newMode !== null) {
                setViewMode(newMode);
              }
            }}
            aria-label="view mode"
          >
            <ToggleButton value="edit" aria-label="edit mode">
              <EditIcon sx={{ mr: 1 }} />
              Edit
            </ToggleButton>
            <ToggleButton value="preview" aria-label="preview mode">
              <PreviewIcon sx={{ mr: 1 }} />
              Preview
            </ToggleButton>
          </ToggleButtonGroup>
        </Box>

        {/* 主要内容区域 */}
        <Box sx={{ 
        minHeight: 'calc(100vh - 200px)',
        bgcolor: 'background.paper',
        borderRadius: 2,
        p: 2,
        overflowX: 'auto'
      }}>
        {/* 使用独立的Box组件而不是Fade */}
        <Box sx={{ display: viewMode === 'edit' ? 'block' : 'none' }}>
          {startDate && endDate ? (
            <TimelineView
              startDate={startDate}
              endDate={endDate}
              selectedPlaces={selectedPlaces || []}
              onEventsUpdate={handleEventsUpdate}
            />
          ) : (
            <Box sx={{
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              <Typography color="text.secondary">
                Please set the date range to start planning
              </Typography>
            </Box>
          )}
        </Box>

        <Box sx={{ display: viewMode === 'preview' ? 'block' : 'none' }}>
          <TimelinePreview events={events} />
        </Box>
        </Box>
      </Box>

      {/* 编辑对话框 */}
      <Dialog 
        open={isEditDialogOpen} 
        onClose={() => setIsEditDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Edit Trip Details</DialogTitle>
        <DialogContent>
          <Grid container spacing={3} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Trip Name"
                value={editValues.tripName}
                onChange={(e) => setEditValues(prev => ({ ...prev, tripName: e.target.value }))}
              />
            </Grid>
            
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Number of People</InputLabel>
                <Select
                  value={editValues.peopleCount}
                  label="Number of People"
                  onChange={(e) => setEditValues(prev => ({ ...prev, peopleCount: e.target.value }))}
                >
                  {[1, 2, 3, 4, 5, 6, 7, 8].map(num => (
                    <MenuItem key={num} value={num}>
                      {num} {num === 1 ? 'person' : 'people'}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <DatePicker
                label="Start Date"
                value={editValues.startDate}
                onChange={(newValue) => setEditValues(prev => ({ ...prev, startDate: newValue }))}
                sx={{ width: '100%' }}
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <DatePicker
                label="End Date"
                value={editValues.endDate}
                onChange={(newValue) => setEditValues(prev => ({ ...prev, endDate: newValue }))}
                sx={{ width: '100%' }}
              />
            </Grid>
            
            <Grid item xs={12}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Transportation Mode
              </Typography>
              <ToggleButtonGroup
                value={editValues.transportMode}
                exclusive
                onChange={(e, newMode) => {
                  if (newMode !== null) {
                    setEditValues(prev => ({ ...prev, transportMode: newMode }));
                  }
                }}
                fullWidth
              >
                <ToggleButton value="walking">
                  <DirectionsWalk sx={{ mr: 1 }} />
                  Walking
                </ToggleButton>
                <ToggleButton value="transit">
                  <DirectionsTransit sx={{ mr: 1 }} />
                  Transit
                </ToggleButton>
                <ToggleButton value="driving">
                  <DirectionsCar sx={{ mr: 1 }} />
                  Driving
                </ToggleButton>
              </ToggleButtonGroup>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setIsEditDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSave} variant="contained">Save</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default TripPlanningPage;