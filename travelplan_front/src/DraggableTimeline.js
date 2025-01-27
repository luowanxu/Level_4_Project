import React, { useState, useEffect } from 'react';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import {
    Box,
    List,
    ListItem,
    Card,
    Typography,
    IconButton,
    Paper,
    SpeedDial,
    SpeedDialIcon,
    SpeedDialAction,
    Alert,
    Snackbar,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    TextField,
    Grid,
  } from '@mui/material';
import {
  AccessTime,
  Place,
  Star,
  Autorenew as AutorenewIcon,
  Edit,
  DirectionsWalk,
  DirectionsCar,
  DirectionsTransit,
} from '@mui/icons-material';

const getTypeStyles = (place) => {
  const type = place?.types?.includes('lodging') ? 'hotel' 
             : place?.types?.includes('tourist_attraction') ? 'attraction'
             : place?.types?.includes('restaurant') ? 'restaurant'
             : 'default';

  switch (type) {
    case 'restaurant':
      return { backgroundColor: '#FF9800', borderColor: '#F57C00' };
    case 'attraction':
      return { backgroundColor: '#4CAF50', borderColor: '#388E3C' };
    case 'hotel':
      return { backgroundColor: '#2196F3', borderColor: '#1976D2' };
    default:
      return { backgroundColor: '#9C27B0', borderColor: '#7B1FA2' };
  }
};





const ScheduleWarningDialog = ({ warnings, open, onClose }) => {
  if (!warnings || warnings.length === 0) return null;

  const getWarningIcon = (severity) => {
    switch (severity) {
      case 'severe':
        return '🔴';
      case 'warning':
        return '⚠️';
      default:
        return 'ℹ️';
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
    >
      <DialogTitle sx={{
        bgcolor: 'warning.main',
        color: 'warning.contrastText',
      }}>
        Schedule Arrangement Warning
      </DialogTitle>
      <DialogContent sx={{ mt: 2 }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {warnings.map((warning, index) => (
            <Alert
              key={index}
              severity={warning.type === 'error' ? 'error' : 
                       warning.severity === 'severe' ? 'error' : 'warning'}
              sx={{ '& .MuiAlert-message': { width: '100%' } }}
            >
              <Box>
                <Typography variant="subtitle1" sx={{ fontWeight: 'medium', mb: 0.5 }}>
                  {getWarningIcon(warning.severity)} {warning.message}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Suggestion: {warning.suggestion}
                </Typography>
              </Box>
            </Alert>
          ))}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} color="primary">
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};






const TransitEvent = ({ duration, mode, startTime, endTime }) => (
  <Paper 
    elevation={1} 
    sx={{ 
      p: 1,
      my: 1,
      display: 'flex',
      alignItems: 'center',
      bgcolor: 'background.paper',
      border: '1px dashed grey'
    }}
  >
    {mode === 'walking' ? <DirectionsWalk /> : 
     mode === 'driving' ? <DirectionsCar /> : 
     <DirectionsTransit />}
    <Box sx={{ ml: 1 }}>
      <Typography variant="body2">
        {startTime} - {endTime}
      </Typography>
      <Typography variant="caption" color="text.secondary">
        {Math.round(duration)} min
      </Typography>
    </Box>
  </Paper>
);

const EventDialog = ({ event, open, onClose, onSave, isManualMode }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedEvent, setEditedEvent] = useState(null);

  useEffect(() => {
    if (event) {
      setEditedEvent(event);
    }
  }, [event]);

  const handleSave = () => {
    onSave(editedEvent);
    setIsEditing(false);
  };

  if (!event || !editedEvent) return null;

  const styles = getTypeStyles(event.place);

  return (
    <Dialog 
      open={open} 
      onClose={() => {
        onClose();
        setIsEditing(false);
      }} 
      maxWidth="sm" 
      fullWidth
    >
      <DialogTitle sx={{ 
        bgcolor: styles.backgroundColor,
        color: 'white',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        {isEditing ? (
          <TextField
            value={editedEvent.title}
            onChange={(e) => setEditedEvent(prev => ({ ...prev, title: e.target.value }))}
            sx={{ 
              input: { color: 'white' },
              '& .MuiOutlinedInput-root': {
                '& fieldset': { borderColor: 'white' },
                '&:hover fieldset': { borderColor: 'white' },
              }
            }}
          />
        ) : (
          <Typography variant="h6">{event.title}</Typography>
        )}
        {isManualMode && (
          <IconButton 
            color="inherit"
            onClick={() => setIsEditing(!isEditing)}
          >
            <Edit />
          </IconButton>
        )}
      </DialogTitle>
      <DialogContent sx={{ mt: 2 }}>
        <Grid container spacing={3}>
          {/* 时间信息 */}
          {event.startTime && event.endTime && (
            <Grid item xs={12}>
              <Paper elevation={0} sx={{ p: 2, bgcolor: 'grey.50' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <AccessTime sx={{ mr: 1, color: 'text.secondary' }} />
                  {isEditing ? (
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <TextField
                        fullWidth
                        label="Start Time"
                        value={editedEvent.startTime}
                        onChange={(e) => setEditedEvent(prev => ({ 
                          ...prev, 
                          startTime: e.target.value 
                        }))}
                      />
                    </Grid>
                    <Grid item xs={6}>
                      <TextField
                        fullWidth
                        label="End Time"
                        value={editedEvent.endTime}
                        onChange={(e) => setEditedEvent(prev => ({ 
                          ...prev, 
                          endTime: e.target.value 
                        }))}
                      />
                    </Grid>
                  </Grid>
                ) : (
                  <Typography>
                    {event.startTime} - {event.endTime}
                  </Typography>
                )}
              </Box>
            </Paper>
          </Grid>
          )}

          {/* 地点信息 */}
          {event.place && (
            <Grid item xs={12}>
              <Paper elevation={0} sx={{ p: 2, bgcolor: 'grey.50' }}>
                <Box sx={{ display: 'flex', alignItems: 'flex-start' }}>
                  <Place sx={{ mr: 1, mt: 0.5, color: 'text.secondary' }} />
                  <Box>
                    <Typography variant="subtitle1" gutterBottom>
                      Location Details
                    </Typography>
                    <Typography variant="body2" color="text.secondary" paragraph>
                      {event.place.vicinity}
                    </Typography>
                    {event.place.rating && (
                      <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                        <Star sx={{ mr: 0.5, color: 'warning.main' }} />
                        <Typography variant="body2">
                          {event.place.rating} / 5
                        </Typography>
                      </Box>
                    )}
                    {event.place.opening_hours && (
                      <Box sx={{ mt: 1 }}>
                        <Typography variant="body2" color="text.secondary">
                          {event.place.opening_hours.open_now ? 
                            '✓ Open now' : 
                            '× Closed now'}
                        </Typography>
                      </Box>
                    )}
                  </Box>
                </Box>
              </Paper>
            </Grid>
          )}
        </Grid>
      </DialogContent>
      <DialogActions>
        <Button 
          onClick={() => {
            onClose();
            setIsEditing(false);
          }}
        >
          Close
        </Button>
        {isEditing && (
          <Button 
            onClick={handleSave} 
            variant="contained"
            sx={{ bgcolor: styles.backgroundColor }}
          >
            Save Changes
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

const DraggableTimeline = ({ 
  startDate, 
  endDate, 
  events,
  onEventsUpdate,
  transportMode,
  isManualMode,
  onModeChange,
  scheduleStatus
}) => {
  const [showSnackbar, setShowSnackbar] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [eventDialogOpen, setEventDialogOpen] = useState(false);
  const [warningDialogOpen, setWarningDialogOpen] = useState(false);

  useEffect(() => {
    if (scheduleStatus?.warnings?.length > 0) {
      setWarningDialogOpen(true);
    }
  }, [scheduleStatus]);

  // 按天分组事件
  const eventsByDay = events.reduce((acc, event) => {
    const day = event.day;
    if (!acc[day]) acc[day] = [];
    acc[day].push(event);
    return acc;
  }, {});

  const onDragEnd = (result) => {
    if (!result.destination || !isManualMode) return;

    const sourceDay = parseInt(result.source.droppableId);
    const destDay = parseInt(result.destination.droppableId);
    const sourceIndex = result.source.index;
    const destIndex = result.destination.index;

    const newEvents = [...events];
    const [movedEvent] = newEvents.splice(
      newEvents.findIndex(e => 
        e.day === sourceDay && 
        eventsByDay[sourceDay][sourceIndex].id === e.id
      ), 1
    );

    movedEvent.day = destDay;
    const insertIndex = newEvents.findIndex(e => 
      e.day === destDay && 
      eventsByDay[destDay][destIndex]?.id === e.id
    );
    
    newEvents.splice(insertIndex === -1 ? newEvents.length : insertIndex, 0, movedEvent);
    onEventsUpdate(newEvents);
  };

  const days = endDate ? Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24)) + 1 : 0;

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <DragDropContext onDragEnd={onDragEnd}>
        <Box sx={{ display: 'flex', gap: 2, p: 2, flexGrow: 1, overflowX: 'auto' }}>
          {Array.from({ length: days }).map((_, dayIndex) => (
            <Paper 
              key={dayIndex}
              elevation={3}
              sx={{ 
                width: 350,
                minWidth: 350,
                display: 'flex',
                flexDirection: 'column',
                p: 2
              }}
            >
              <Typography variant="h6" gutterBottom>
                Day {dayIndex + 1}
              </Typography>
              <Droppable droppableId={dayIndex.toString()}>
                {(provided) => (
                  <List
                    ref={provided.innerRef}
                    {...provided.droppableProps}
                    sx={{ flexGrow: 1 }}
                  >
                    {eventsByDay[dayIndex]?.map((event, index) => (
                      <React.Fragment key={event.id}>
                        {event.type !== 'transit' ? (
                          <Draggable
                            draggableId={event.id}
                            index={index}
                            isDragDisabled={!isManualMode}
                          >
                            {(provided) => (
                              <ListItem
                                ref={provided.innerRef}
                                {...provided.draggableProps}
                                {...provided.dragHandleProps}
                                sx={{ px: 0 }}
                              >
                                <Card
                                  elevation={3}
                                  onClick={() => {
                                    setSelectedEvent(event);
                                    setEventDialogOpen(true);
                                  }}
                                  sx={{
                                    cursor: 'pointer',
                                    width: '100%',
                                    p: 2,
                                    bgcolor: getTypeStyles(event.place).backgroundColor,
                                    color: 'white',
                                    opacity: isManualMode ? 1 : 0.8
                                  }}
                                >
                                  <Typography variant="h6">{event.title}</Typography>
                                  {/* 仅当时间不为空时显示时间信息 */}
                                  {event.startTime && event.endTime && (
                                    <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                                      <AccessTime sx={{ mr: 1 }} />
                                      <Typography>
                                        {event.startTime} - {event.endTime}
                                      </Typography>
                                    </Box>
                                  )}
                                  {event.place?.vicinity && (
                                    <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                                      <Place sx={{ mr: 1 }} />
                                      <Typography noWrap>
                                        {event.place.vicinity}
                                      </Typography>
                                    </Box>
                                  )}
                                </Card>
                              </ListItem>
                            )}
                          </Draggable>
                        ) : (
                          <TransitEvent
                            startTime={event.startTime}
                            endTime={event.endTime}
                            duration={event.duration}
                            mode={transportMode}
                          />
                        )}
                      </React.Fragment>
                    ))}
                    {provided.placeholder}
                  </List>
                )}
              </Droppable>
            </Paper>
          ))}
        </Box>
      </DragDropContext>

      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
        <Button
          variant="outlined"
          startIcon={isManualMode ? <AutorenewIcon /> : <Edit />}
          onClick={() => {
            onModeChange(!isManualMode);
            setShowSnackbar(true);
          }}
        >
          {isManualMode ? "Switch to Automatic" : "Switch to Manual"}
        </Button>
      </Box>

      <Snackbar
        open={showSnackbar}
        autoHideDuration={4000}
        onClose={() => setShowSnackbar(false)}
      >
        <Alert 
          severity="info" 
          onClose={() => setShowSnackbar(false)}
        >
          {isManualMode ? 
            'Switched to manual mode. You can now drag to reorder events.' :
            'Switched to automatic mode. Schedule will be optimized.'
          }
        </Alert>
      </Snackbar>

      <EventDialog
        event={selectedEvent}
        open={eventDialogOpen}
        onClose={() => setEventDialogOpen(false)}
        isManualMode={isManualMode}
        onSave={(updatedEvent) => {
          const newEvents = events.map(e => 
            e.id === updatedEvent.id ? updatedEvent : e
          );
          onEventsUpdate(newEvents);
        }}
      />
      <ScheduleWarningDialog
        warnings={scheduleStatus?.warnings}
        open={warningDialogOpen}
        onClose={() => setWarningDialogOpen(false)}
      />
    </Box>
  );
};

export default DraggableTimeline;