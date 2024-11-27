// TimelinePreview.js
import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Avatar,
  Chip,
  Tooltip,
  IconButton
} from '@mui/material';
import {
  AccessTime as TimeIcon,
  Place as PlaceIcon,
  NavigateNext as NextIcon,
} from '@mui/icons-material';

const TimelinePreview = ({ events }) => {
    // 按天分组并排序事件
    const eventsByDay = events.reduce((acc, event) => {
      const day = event.day;
      if (!acc[day]) {
        acc[day] = [];
      }
      acc[day].push(event);
      return acc;
    }, {});


    const getTypeStyles = (place) => {
        const type = place?.types?.includes('lodging') ? 'hotel' 
                   : place?.types?.includes('tourist_attraction') ? 'attraction'
                   : place?.types?.includes('restaurant') ? 'restaurant'
                   : 'default';
      
        switch (type) {
          case 'restaurant':
            return {
              backgroundColor: '#FF9800',
              hoverColor: '#F57C00',
              dialogColor: '#FFB74D'
            };
          case 'attraction':
            return {
              backgroundColor: '#4CAF50',
              hoverColor: '#388E3C',
              dialogColor: '#81C784'
            };
          case 'hotel':
            return {
              backgroundColor: '#2196F3',
              hoverColor: '#1976D2',
              dialogColor: '#64B5F6'
            };
          default:
            return {
              backgroundColor: '#9C27B0',
              hoverColor: '#7B1FA2',
              dialogColor: '#BA68C8'
            };
        }
      };



    Object.keys(eventsByDay).forEach(day => {
        eventsByDay[day].sort((a, b) => {
          // 将时间转换为24小时制进行比较
          const getHour = (timeStr) => {
            const [time, period] = timeStr.split(' ');
            let [hour] = time.split(':').map(Number);
            if (period === 'PM' && hour !== 12) hour += 12;
            if (period === 'AM' && hour === 12) hour = 0;
            return hour;
          };
    
          const aHour = getHour(a.startTime);
          const bHour = getHour(b.startTime);
          return aHour - bHour;
        });
      });



      return (
        <Box sx={{ 
          width: '100%',
          overflowX: 'auto',
          py: 4
        }}>
          {Object.entries(eventsByDay).map(([day, dayEvents], dayIndex) => (
        <Box
          key={day}
          sx={{
            mb: 4,
            position: 'relative'
          }}
        >
          <Typography 
            variant="h6" 
            sx={{ 
              mb: 2,
              color: 'primary.main',
              fontWeight: 'bold'
            }}
          >
            Day {Number(day) + 1}
          </Typography>

          <Box sx={{
            display: 'flex',
            alignItems: 'flex-start',
            position: 'relative',
            '&::before': {
              content: '""',
              position: 'absolute',
              left: '24px',
              top: 0,
              bottom: 0,
              width: '2px',
              bgcolor: 'primary.light',
              zIndex: 0
            }
          }}>
            {dayEvents.map((event, index) => (
              <Box
                key={event.id}
                sx={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  mb: 2,
                  flex: 1,
                  position: 'relative'
                }}
              >
                <Avatar
                  sx={{
                    bgcolor: 'primary.main',
                    width: 50,
                    height: 50,
                    mr: 2,
                    zIndex: 1
                  }}
                >
                  {event.startTime.split(':')[0]}
                </Avatar>

                <Paper
                  elevation={2}
                  sx={{
                    p: 2,
                    flex: 1,
                    borderRadius: 2,
                    position: 'relative',
                    bgcolor: `${getTypeStyles(event.place).backgroundColor}15`, // 添加半透明背景色
                    borderLeft: `4px solid ${getTypeStyles(event.place).backgroundColor}`, // 添加左侧色条
                    '&::before': {
                      content: '""',
                      position: 'absolute',
                      left: -10,
                      top: 20,
                      width: 20,
                      height: 20,
                      bgcolor: 'background.paper',
                      transform: 'rotate(45deg)',
                      zIndex: 0
                    },
                    // 添加hover效果
                    '&:hover': {
                      bgcolor: `${getTypeStyles(event.place).backgroundColor}25`,
                      transition: 'background-color 0.3s ease'
                    }
                  }}
                >
                  <Typography variant="h6" gutterBottom>
                    {event.title}
                  </Typography>
                  
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <TimeIcon sx={{ fontSize: 16, mr: 1, color: 'text.secondary' }} />
                    <Typography variant="body2" color="text.secondary">
                      {event.startTime} - {event.endTime}
                    </Typography>
                  </Box>

                  {event.place && event.place.vicinity && (
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <PlaceIcon sx={{ fontSize: 16, mr: 1, color: 'text.secondary' }} />
                      <Typography variant="body2" color="text.secondary">
                        {event.place.vicinity}
                      </Typography>
                    </Box>
                  )}

                  {event.place && event.place.rating && (
                    <Box sx={{ mt: 1 }}>
                      <Chip 
                        size="small"
                        label={`Rating: ${event.place.rating}`}
                        color="primary"
                        variant="outlined"
                      />
                    </Box>
                  )}
                </Paper>

                {index < dayEvents.length - 1 && (
                  <Box sx={{ 
                    position: 'absolute',
                    left: 24,
                    bottom: -30,
                    zIndex: 2
                  }}>
                    <NextIcon color="primary" />
                  </Box>
                )}
              </Box>
            ))}
          </Box>
        </Box>
      ))}
    </Box>
  );
};

export default TimelinePreview;