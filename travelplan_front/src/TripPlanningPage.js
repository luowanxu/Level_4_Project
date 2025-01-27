import React, { useState, useEffect } from 'react';
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
  ToggleButtonGroup,
  ToggleButton,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers';
import {
  ArrowBack,
  Edit,
  DirectionsWalk,
  DirectionsCar,
  DirectionsTransit,
  EditCalendar as EditIcon,
  Preview as PreviewIcon,
} from '@mui/icons-material';
import DraggableTimeline from './DraggableTimeline';
import TimelinePreview from './TimelinePreview';
import axios from 'axios';

const TripPlanningPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { selectedPlaces } = location.state || { selectedPlaces: [] };
  const [events, setEvents] = useState([]);
  const [viewMode, setViewMode] = useState('edit');
  const [isManualMode, setIsManualMode] = useState(false);

  const [tripName, setTripName] = useState('My Trip');
  const [peopleCount, setPeopleCount] = useState(1);
  const [startDate, setStartDate] = useState(null);
  const [endDate, setEndDate] = useState(null);
  const [transportMode, setTransportMode] = useState('walking');
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [editValues, setEditValues] = useState({
    tripName,
    peopleCount,
    startDate,
    endDate,
    transportMode,
  });
  const [scheduleStatus, setScheduleStatus] = useState(null);  // 添加这个状态
  const [isFirstVisit, setIsFirstVisit] = useState(true);
  const { cityName, region, country } = location.state || {};

  useEffect(() => {
    const initializeTimeline = async () => {
      if (!startDate || !endDate || !selectedPlaces?.length) return;
    
      try {
        const response = await axios.post('/api/cluster-places/', {
          places: selectedPlaces,
          startDate: startDate.toISOString().split('T')[0],
          endDate: endDate.toISOString().split('T')[0],
          transportMode: transportMode
        });
    
        // 更新状态，即使在失败的情况下也要处理 schedule_status
        if (response.data.schedule_status) {
          setScheduleStatus(response.data.schedule_status);
        }
    
        if (response.data.success) {
          setEvents(response.data.events);
          setIsManualMode(false);
        }
      } catch (error) {
        console.error('Failed to initialize timeline:', error);
        // 设置一个默认的错误状态
        setScheduleStatus({
          is_reasonable: false,
          warnings: [{
            type: 'error',
            message: 'Failed to generate schedule',
            suggestion: 'Please try adjusting your selection or try again later'
          }],
          severity: 'severe'
        });
      }
    };

    initializeTimeline();
    if (isFirstVisit) {
      setIsEditDialogOpen(true);
      setIsFirstVisit(false);
    }
  }, [startDate, endDate, selectedPlaces, transportMode, isFirstVisit]);

  const handleModeChange = async (newManualMode) => {
    if (!newManualMode) {  // 切换到自动模式
      try {
        // 使用与初始化相同的API重新生成日程
        const response = await axios.post('/api/cluster-places/', {
          places: selectedPlaces,
          startDate: startDate.toISOString().split('T')[0],
          endDate: endDate.toISOString().split('T')[0],
          transportMode: transportMode
        });
  
        if (response.data.success) {
          setEvents(response.data.events);
          if (response.data.schedule_status) {
            setScheduleStatus(response.data.schedule_status);
          }
        }
      } catch (error) {
        console.error('Failed to optimize route:', error);
        setScheduleStatus({
          is_reasonable: false,
          warnings: [{
            type: 'error',
            message: 'Failed to optimize schedule',
            suggestion: 'Please try again or remain in manual mode'
          }],
          severity: 'warning'
        });
      }
    }
    setIsManualMode(newManualMode);
  };

  const handleEventsUpdate = (newEvents) => {
    setEvents(newEvents);
  };

  const handleSave = () => {
    setTripName(editValues.tripName);
    setPeopleCount(editValues.peopleCount);
    setStartDate(editValues.startDate);
    setEndDate(editValues.endDate);
    setTransportMode(editValues.transportMode);
    setIsEditDialogOpen(false);
  };

  // TripPlanningPage.js
  const handleBack = () => {
    navigate('/selection', { 
      state: { 
        cityName,
        region,
        country,
        preservedSelectedPlaces: selectedPlaces,
        placesData: location.state.placesData
      } 
    });
  };

  return (
    <Container maxWidth={false} sx={{ px: 3 }}>
      <Box sx={{ py: 4 }}>
        {/* Header */}
        <Box display="flex" alignItems="flex-start" mb={4}>
          <IconButton onClick={handleBack} sx={{ mr: 2 }}>
            <ArrowBack />
          </IconButton>
          
          <Box sx={{ flexGrow: 1 }}>
            <Box display="flex" alignItems="center" mb={1}>
              <Typography variant="h4" component="h1" sx={{ flexGrow: 1 }}>
                {tripName}
              </Typography>
              <IconButton onClick={() => setIsEditDialogOpen(true)} size="small">
                <Edit />
              </IconButton>
            </Box>
            
            <Typography variant="subtitle1" color="text.secondary" gutterBottom>
              {peopleCount} {peopleCount === 1 ? 'person' : 'people'} • 
              {transportMode === 'walking' ? ' Walking' :
               transportMode === 'driving' ? ' Driving' : ' Public Transit'}
            </Typography>
            <Typography variant="subtitle1" color="text.secondary">
              {startDate && endDate ? 
                `${startDate.toLocaleDateString()} - ${endDate.toLocaleDateString()}` : 
                'Dates not set'}
            </Typography>
          </Box>
        </Box>

        {/* View Mode Toggle */}
        <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>
          <ToggleButtonGroup
            value={viewMode}
            exclusive
            onChange={(e, newMode) => newMode && setViewMode(newMode)}
          >
            <ToggleButton value="edit">
              <EditIcon sx={{ mr: 1 }} />
              Edit
            </ToggleButton>
            <ToggleButton value="preview">
              <PreviewIcon sx={{ mr: 1 }} />
              Preview
            </ToggleButton>
          </ToggleButtonGroup>
        </Box>

        {/* Main Content */}
        <Box sx={{ 
          minHeight: 'calc(100vh - 200px)',
          bgcolor: 'background.paper',
          borderRadius: 2,
          p: 2,
          overflowX: 'auto'
        }}>
          {viewMode === 'edit' ? (
            startDate && endDate ? (
              <DraggableTimeline
                startDate={startDate}
                endDate={endDate}
                events={events}
                onEventsUpdate={handleEventsUpdate}
                transportMode={transportMode}
                isManualMode={isManualMode}
                onModeChange={handleModeChange}
                scheduleStatus={scheduleStatus} // 从后端响应中获取
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
            )
          ) : (
            <TimelinePreview events={events} />
          )}
        </Box>
      </Box>

      {/* Edit Dialog */}
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
                onChange={(e) => setEditValues(prev => ({ 
                  ...prev, 
                  tripName: e.target.value 
                }))}
              />
            </Grid>
            
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Number of People</InputLabel>
                <Select
                  value={editValues.peopleCount}
                  label="Number of People"
                  onChange={(e) => setEditValues(prev => ({ 
                    ...prev, 
                    peopleCount: e.target.value 
                  }))}
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
                onChange={(newValue) => setEditValues(prev => ({ 
                  ...prev, 
                  startDate: newValue 
                }))}
                sx={{ width: '100%' }}
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <DatePicker
                label="End Date"
                value={editValues.endDate}
                onChange={(newValue) => setEditValues(prev => ({ 
                  ...prev, 
                  endDate: newValue 
                }))}
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
                onChange={(e, newMode) => newMode && setEditValues(prev => ({ 
                  ...prev, 
                  transportMode: newMode 
                }))}
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