import React, { useState } from 'react';
import axios from 'axios';
import {
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineConnector,
  TimelineContent,
  TimelineOppositeContent,
  TimelineDot
} from '@mui/lab';
import {
  Box,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Card,
  CardContent,
  LinearProgress,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  ExpandMore,
  Restaurant,
  Hotel,
  Attractions,
  Map,
  Share,
  SaveAlt,
  DirectionsWalk,
  DirectionsCar,
  DirectionsTransit,
} from '@mui/icons-material';
import FixedMapDialog from './FixedMapDialog'; // 导入修复版的地图对话框

const TimelinePreview = ({ events }) => {
  console.log('TimelinePreview transit events:', events.filter(e => e.type === 'transit'));
  const [expanded, setExpanded] = useState(false);
  const [mapOpen, setMapOpen] = useState(false); // 控制地图对话框状态
  
  const getEventIcon = (event) => {
    if (event.type === 'transit') {
      switch (event.mode) {
        case 'walking':
          return <DirectionsWalk />;
        case 'driving':
          return <DirectionsCar />;
        case 'transit':
          return <DirectionsTransit />;
        default:
          return <DirectionsWalk />;
      }
    }
    
    if (!event.place?.types) return <Attractions />;
    if (event.place.types.includes('lodging')) return <Hotel />;
    if (event.place.types.includes('restaurant')) return <Restaurant />;
    if (event.place.types.includes('tourist_attraction')) return <Attractions />;
    return <Attractions />;
  };

  const getEventColor = (event) => {
    if (event.type === 'transit') return 'grey';
    if (!event.place?.types) return 'secondary';
    if (event.place.types.includes('lodging')) return 'info';
    if (event.place.types.includes('restaurant')) return 'warning';
    if (event.place.types.includes('tourist_attraction')) return 'success';
    return 'secondary';
  };

  const handleExportCalendar = async () => {
    try {
      const response = await axios.post('/api/export-calendar/', { events }, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'trip-schedule.ics');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Failed to export calendar:', error);
    }
  };

  // 打开和关闭地图对话框
  const handleOpenMap = () => {
    console.log("Opening map dialog");
    console.log("Total events:", events.length);
    console.log("Place events:", events.filter(e => e.type !== 'transit').length);
    console.log("Sample place event:", events.find(e => e.type !== 'transit'));
    setMapOpen(true);
  };

  const handleCloseMap = () => {
    setMapOpen(false);
  };

  const eventsByDay = events.reduce((acc, event) => {
    const day = event.day;
    if (!acc[day]) acc[day] = [];
    acc[day].push(event);
    return acc;
  }, {});

  const calculateDayProgress = (events) => {
    const dayStart = 8;
    const dayEnd = 22;
    const totalHours = dayEnd - dayStart;
    let usedHours = 0;

    events.forEach(event => {
      const [startHour] = event.startTime.split(':');
      const [endHour] = event.endTime.split(':');
      usedHours += endHour - startHour;
    });

    return (usedHours / totalHours) * 100;
  };

  const getTransitModeName = (mode) => {
    switch (mode) {
      case 'walking':
        return 'Walking';
      case 'driving':
        return 'Driving';
      case 'transit':
        return 'Public Transit';
      default:
        return 'Transit';
    }
  };
  
  const renderTransitContent = (event) => (
    <Card 
      variant="outlined"
      sx={{ 
        bgcolor: 'grey.100',
        border: '1px dashed grey'
      }}
    >
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {getEventIcon(event)}
          <Box>
            <Typography variant="subtitle1">
              {getTransitModeName(event.mode)}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Duration: {Math.round(event.duration)} minutes
            </Typography>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  const renderEventContent = (event) => (
    <Card 
      variant="outlined"
      sx={{ 
        bgcolor: (theme) => `${theme.palette[getEventColor(event)].light}15`,
        backdropFilter: 'blur(8px)',
        border: (theme) => `1px solid ${theme.palette[getEventColor(event)].main}30`
      }}
    >
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Typography variant="h6" gutterBottom>
            {event.title}
          </Typography>
        </Box>

        {event.place?.vicinity && (
          <Typography variant="body2" color="text.secondary" gutterBottom>
            {event.place.vicinity}
          </Typography>
        )}

        {event.place?.rating && (
          <Box sx={{ mt: 1 }}>
            <Chip 
              size="small"
              label={`Rating: ${event.place.rating}`}
              color={getEventColor(event)}
              variant="outlined"
            />
          </Box>
        )}
      </CardContent>
    </Card>
  );

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
        <Tooltip title="View on Map">
          <IconButton onClick={handleOpenMap}><Map /></IconButton>
        </Tooltip>
        <Tooltip title="Share Itinerary">
          <IconButton><Share /></IconButton>
        </Tooltip>
        <Tooltip title="Save as iCal">
          <IconButton onClick={handleExportCalendar}><SaveAlt /></IconButton>
        </Tooltip>
      </Box>

      {/* 使用修复版的地图对话框组件 */}
      <FixedMapDialog
        open={mapOpen}
        handleClose={handleCloseMap}
        events={events}
        eventsByDay={eventsByDay}
      />

      {Object.entries(eventsByDay).map(([day, dayEvents]) => (
        <Accordion 
          key={day}
          expanded={expanded === `day${day}`}
          onChange={() => setExpanded(expanded === `day${day}` ? false : `day${day}`)}
        >
          <AccordionSummary expandIcon={<ExpandMore />}>
            <Box sx={{ width: '100%' }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="h6">Day {Number(day) + 1}</Typography>
                <Chip 
                  label={`${dayEvents.filter(event => event.place?.types).length} Activities`}
                  size="small"
                  color="primary"
                />
              </Box>
              <LinearProgress 
                variant="determinate" 
                value={calculateDayProgress(dayEvents)}
                sx={{ height: 8, borderRadius: 4 }}
              />
            </Box>
          </AccordionSummary>

          <AccordionDetails>
            <Timeline position="alternate">
              {dayEvents.map((event, index) => (
                <TimelineItem key={event.id}>
                  <TimelineOppositeContent>
                    <Typography variant="h6" color="text.secondary">
                      {event.startTime}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {event.endTime}
                    </Typography>
                  </TimelineOppositeContent>
                  
                  <TimelineSeparator>
                    <TimelineDot color={getEventColor(event)}>
                      {getEventIcon(event)}
                    </TimelineDot>
                    {index < dayEvents.length - 1 && <TimelineConnector />}
                  </TimelineSeparator>
                  
                  <TimelineContent>
                    {event.type === 'transit' ? 
                      renderTransitContent(event) : 
                      renderEventContent(event)}
                  </TimelineContent>
                </TimelineItem>
              ))}
            </Timeline>
          </AccordionDetails>
        </Accordion>
      ))}
    </Box>
  );
};

export default TimelinePreview;