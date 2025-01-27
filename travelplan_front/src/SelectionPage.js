import React, { useState, useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Container,
  Box,
  Typography,
  Tabs,
  Tab,
  Grid,
  Alert,
  IconButton,
  TextField,
  InputAdornment,
  Button,
  FormControl,
  Select,
  MenuItem,
  Chip,
  Stack,
  Rating,
} from '@mui/material';
import RestaurantIcon from '@mui/icons-material/Restaurant';
import HotelIcon from '@mui/icons-material/Hotel';
import AttractionsIcon from '@mui/icons-material/Attractions';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import SearchIcon from '@mui/icons-material/Search';
import SortIcon from '@mui/icons-material/Sort';
import FilterListIcon from '@mui/icons-material/FilterList';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import AddIcon from '@mui/icons-material/Add';
import PlaceCard from './PlaceCard';
import SelectedPlacesSidebar from './SelectedPlacesSidebar'; // 确保创建了这个文件
import PageTour from './PageTour'; // 如果在同一目录
import { useTheme } from '@mui/material'

// 定义抽屉宽度常量
const DRAWER_WIDTH = 350;
const Z_INDEX = {
  DRAWER: 1300,      // 提高侧边栏的 z-index
  TOGGLE: 1301,      // 切换按钮稍高于侧边栏
  CONTENT: 1         // 主内容保持不变
};

// TabPanel 组件定义
function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const SelectionPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { cityName, region, country, placesData: initialPlacesData, preservedSelectedPlaces } = location.state || {};
  const [placesData, setPlacesData] = useState(initialPlacesData || { restaurants: [], attractions: [], hotels: [] });
  const theme = useTheme();
  
  
  // 状态管理
  const [tabValue, setTabValue] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('rating');
  const [filters, setFilters] = useState({
    minRating: 0,
    priceLevel: [],
    types: [],
    openNow: false
  });
  const [selectedPlaces, setSelectedPlaces] = useState(preservedSelectedPlaces || []);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  

  // 添加处理选择的函数
  const handlePlaceSelect = (place) => {
    setSelectedPlaces(prev => {
      const isAlreadySelected = prev.some(p => p.place_id === place.place_id);
      if (isAlreadySelected) {
        return prev.filter(p => p.place_id !== place.place_id);
      } else {
        return [...prev, place];
      }
    });
  };

  const handleRemovePlace = (place) => {
    setSelectedPlaces(prev => 
      prev.filter(p => p.place_id !== place.place_id)
    );
  };

  const handleClearAll = () => {
    setSelectedPlaces([]);
  };

  // 1. 先定义必要的辅助函数
  const getCurrentType = () => {
    switch (tabValue) {
      case 0: return 'restaurants';
      case 1: return 'attractions';
      case 2: return 'hotels';
      default: return 'restaurants';
    }
  };

  const getSearchPlaceholder = () => {
    switch (tabValue) {
      case 0: return 'Search restaurants...';
      case 1: return 'Search attractions...';
      case 2: return 'Search hotels...';
      default: return 'Search...';
    }
  };

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
    setSearchQuery('');
  };

  const handleProceed = () => {
    navigate('/plan', { 
      state: { 
        cityName,
        region,
        country,
        placesData, // 确保这里传递了完整的 placesData
        selectedPlaces,
        // 如果计划页面需要其他数据也可以在这里传递
      } 
    });
  };

  // 2. 然后定义依赖这些函数的 useMemo
  const availableTypes = useMemo(() => {
    if (!placesData) return [];
    const currentType = getCurrentType();
    const places = placesData[currentType] || [];
    
    const types = new Set();
    places.forEach(place => {
      place.types?.forEach(type => {
        if (!['point_of_interest', 'establishment'].includes(type)) {
          types.add(type);
        }
      });
    });
    return Array.from(types);
  }, [placesData, tabValue]);

  const filteredAndSortedPlaces = useMemo(() => {
    if (!placesData) return [];
    
    const currentType = getCurrentType();
    let places = placesData[currentType] || [];
    
    // 搜索过滤
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      places = places.filter(place => {
        const nameMatch = place.name?.toLowerCase().includes(query);
        const typesMatch = place.types?.some(type => 
          type.replace(/_/g, ' ').toLowerCase().includes(query)
        );
        const addressMatch = place.vicinity?.toLowerCase().includes(query);
        return nameMatch || typesMatch || addressMatch;
      });
    }

    // 应用过滤器
    places = places.filter(place => {
      const ratingFilter = place.rating >= filters.minRating;
      const priceFilter = filters.priceLevel.length === 0 || 
        filters.priceLevel.includes(place.price_level);
      const typeFilter = filters.types.length === 0 ||
        place.types?.some(type => filters.types.includes(type));
      const openFilter = !filters.openNow || 
        place.opening_hours?.open_now;
      
      return ratingFilter && priceFilter && typeFilter && openFilter;
    });

    // 排序
    return places.sort((a, b) => {
      switch (sortBy) {
        case 'rating':
          return (b.rating || 0) - (a.rating || 0);
        case 'reviews':
          return (b.user_ratings_total || 0) - (a.user_ratings_total || 0);
        case 'priceAsc':
          return (a.price_level || 0) - (b.price_level || 0);
        case 'priceDesc':
          return (b.price_level || 0) - (a.price_level || 0);
        case 'nameAsc':
          return a.name.localeCompare(b.name);
        case 'nameDesc':
          return b.name.localeCompare(a.name);
        default:
          return 0;
      }
    });
  }, [placesData, tabValue, searchQuery, sortBy, filters]);

  // 3. 其他辅助函数
  const handleClearFilters = () => {
    setFilters({
      minRating: 0,
      priceLevel: [],
      types: [],
      openNow: false
    });
  };

  // 4. 数据可用性检查
  const hasRestaurants = Array.isArray(placesData?.restaurants) && placesData.restaurants.length > 0;
  const hasAttractions = Array.isArray(placesData?.attractions) && placesData.attractions.length > 0;
  const hasHotels = Array.isArray(placesData?.hotels) && placesData.hotels.length > 0;



  const hasSelectedHotel = useMemo(() => {
    return selectedPlaces.some(place => placesData.hotels?.includes(place));
  }, [selectedPlaces, placesData.hotels]);

  return (
    <Box 
      sx={{ 
        display: 'flex',
        minHeight: '100vh',
        backgroundColor: theme.palette.background.default,
      }}
    >
      <SelectedPlacesSidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        selectedPlaces={selectedPlaces}
        onRemovePlace={handleRemovePlace}
        onClearAll={handleClearAll}
        cityName={cityName}
        placesData={placesData}
        zIndex={Z_INDEX.DRAWER}
        onProceed={handleProceed}
      />

      {/* 侧边栏切换按钮 */}
      <IconButton
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="sidebar-toggle"
        sx={{
          position: 'fixed',
          left: sidebarOpen ? DRAWER_WIDTH : 0,
          top: '50%',
          transform: 'translateY(-50%)',
          backgroundColor: 'background.paper',
          borderRadius: '0 4px 4px 0',
          zIndex: Z_INDEX.TOGGLE,
          boxShadow: theme.shadows[2],
          '&:hover': {
            backgroundColor: 'action.hover',
          },
          transition: theme.transitions.create(['left'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.standard,
          }),
        }}
      >
        {sidebarOpen ? <ChevronLeftIcon /> : <ChevronRightIcon />}
      </IconButton>

      {/* 主内容区域 */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          transition: theme.transitions.create(['margin', 'width'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.standard,
          }),
          marginLeft: sidebarOpen ? `${DRAWER_WIDTH}px` : 0,
          width: '100%',
          px: 3, // 添加适度的水平内边距
        }}
      >
        {/* 顶部标题和返回按钮 */}
        <Box sx={{ py: 4 }}>
          <Box display="flex" alignItems="center" mb={4}>
            <IconButton 
              onClick={() => navigate('/')}
              sx={{ mr: 2 }}
            >
              <ArrowBackIcon />
            </IconButton>
            <Box>
              <Typography variant="h4" component="h1">
                Explore {cityName}
                {region && `, ${region}`}
                {country && `, ${country}`}
              </Typography>
              <Typography variant="subtitle1" color="text.secondary">
                Discover places to eat, visit, and stay
              </Typography>
              <Typography 
                variant="subtitle1" 
                color="text.secondary" 
                sx={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: 0.5
                }}
              >
                Click <AddIcon fontSize="small" /> to add interesting places to your list
              </Typography>
            </Box>
          </Box>

          {/* 标签栏 */}
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs 
              value={tabValue} 
              onChange={handleTabChange} 
              centered
              variant="fullWidth"
            >
            <Tab 
              icon={<RestaurantIcon />} 
              label={`Restaurants (${placesData.restaurants?.length || 0})`}
              disabled={!hasRestaurants}
            />
            <Tab 
              icon={<AttractionsIcon />} 
              label={`Attractions (${placesData.attractions?.length || 0})`}
              disabled={!hasAttractions}
            />
            <Tab 
              icon={<HotelIcon />} 
              label={`Hotels (${placesData.hotels?.length || 0})`}
              disabled={!hasHotels}
            />
          </Tabs>
        </Box>
  
        {/* 搜索和筛选部分 - 这里开始是新增的内容 */}
        <Box sx={{ py: 3 }}>
          <Grid container spacing={2}>
            {/* 搜索框 - 样式更新但功能保持不变 */}
            <Grid item xs={12} className="search-filter">
            <TextField
                fullWidth
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={getSearchPlaceholder()}
                variant="outlined"
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                }}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 2,
                    backgroundColor: 'white',
                  },
                }}
              />
            </Grid>
  
            {/* 排序选择器 - 新增 */}
            <Grid item xs={12} sm={6} md={4}>
              <FormControl fullWidth>
                <Select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  startAdornment={
                    <InputAdornment position="start">
                      <SortIcon />
                    </InputAdornment>
                  }
                >
                  <MenuItem value="rating">Rating (High to Low)</MenuItem>
                  <MenuItem value="reviews">Most Reviewed</MenuItem>
                  <MenuItem value="priceAsc">Price (Low to High)</MenuItem>
                  <MenuItem value="priceDesc">Price (High to Low)</MenuItem>
                  <MenuItem value="nameAsc">Name (A to Z)</MenuItem>
                  <MenuItem value="nameDesc">Name (Z to A)</MenuItem>
                </Select>
              </FormControl>
            </Grid>
  
            {/* 价格筛选器 - 新增 */}
            <Grid item xs={12} sm={6} md={4}>
              <FormControl fullWidth>
                <Select
                  multiple
                  value={filters.priceLevel}
                  onChange={(e) => setFilters(prev => ({
                    ...prev,
                    priceLevel: e.target.value
                  }))}
                  renderValue={(selected) => {
                    if (selected.length === 0) {
                      return <Typography color="text.secondary">Price Level</Typography>;
                    }
                    return (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {selected.map((value) => (
                          <Chip 
                            key={value} 
                            label={'£'.repeat(value)} 
                            size="small"
                          />
                        ))}
                      </Box>
                    );
                  }}
                  displayEmpty
                  startAdornment={
                    <InputAdornment position="start">
                      <FilterListIcon />
                    </InputAdornment>
                  }
                  sx={{
                    '& .MuiSelect-select': {
                      display: 'flex',
                      alignItems: 'center',
                      gap: 1
                    }
                  }}
                >
                  <MenuItem value={1}>£ (Inexpensive)</MenuItem>
                  <MenuItem value={2}>££ (Moderate)</MenuItem>
                  <MenuItem value={3}>£££ (Expensive)</MenuItem>
                  <MenuItem value={4}>££££ (Very Expensive)</MenuItem>
                </Select>
              </FormControl>
            </Grid>
  
            {/* 类型筛选器 - 新增 */}
            <Grid item xs={12} md={4}>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <FormControl fullWidth>
                  <Select
                    multiple
                    value={filters.types}
                    onChange={(e) => setFilters(prev => ({
                      ...prev,
                      types: e.target.value
                    }))}
                    renderValue={(selected) => {
                      if (selected.length === 0) {
                        return <Typography color="text.secondary">Categories</Typography>;
                      }
                      return (
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                          {selected.map((value) => (
                            <Chip 
                              key={value} 
                              label={value.replace(/_/g, ' ')} 
                              size="small"
                            />
                          ))}
                        </Box>
                      );
                    }}
                    displayEmpty
                    startAdornment={
                      <InputAdornment position="start">
                        <FilterListIcon />
                      </InputAdornment>
                    }
                    sx={{
                      '& .MuiSelect-select': {
                        display: 'flex',
                        alignItems: 'center',
                        gap: 1
                      }
                    }}
                  >
                    {availableTypes.map(type => (
                      <MenuItem key={type} value={type}>
                        {type.replace(/_/g, ' ')}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                
                <Button 
                  variant="outlined" 
                  onClick={handleClearFilters}
                  sx={{ whiteSpace: 'nowrap' }}
                >
                  Clear
                </Button>
              </Box>
            </Grid>
  
            {/* 评分筛选器 - 新增 */}
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Typography>Minimum Rating:</Typography>
                <Rating
                  value={filters.minRating}
                  onChange={(event, newValue) => {
                    setFilters(prev => ({
                      ...prev,
                      minRating: newValue || 0
                    }));
                  }}
                  precision={0.5}
                />
                {filters.minRating > 0 && (
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => setFilters(prev => ({ ...prev, minRating: 0 }))}
                  >
                    Clear
                  </Button>
                )}
              </Box>
            </Grid>
  
            {/* 活动筛选器展示 - 新增 */}
            <Grid item xs={12}>
              <Stack direction="row" spacing={1} flexWrap="wrap" gap={1}>
                {filters.minRating > 0 && (
                  <Chip 
                    label={`Rating ≥ ${filters.minRating}`}
                    onDelete={() => setFilters(prev => ({ ...prev, minRating: 0 }))}
                  />
                )}
                {filters.openNow && (
                  <Chip 
                    label="Open Now"
                    onDelete={() => setFilters(prev => ({ ...prev, openNow: false }))}
                  />
                )}
              </Stack>
            </Grid>
          </Grid>
        </Box>
  
        {/* 内容展示部分 - 使用新的 filteredAndSortedPlaces 替换原来的 filteredPlaces */}
        <TabPanel value={tabValue} index={0}>
        {hasRestaurants ? (
          filteredAndSortedPlaces.length > 0 ? (
            <Grid container spacing={3}>
              {filteredAndSortedPlaces.map((place, index) => (
                <Grid item xs={12} sm={6} md={4} key={index} className="place-card">
                  <PlaceCard 
                    place={place} 
                    type="restaurant"
                    onSelect={handlePlaceSelect}
                    isSelected={selectedPlaces.some(p => p.place_id === place.place_id)}
                  />
                </Grid>
              ))}
            </Grid>
          ) : (
            <Alert severity="info" sx={{ mt: 2 }}>
              No restaurants found matching your criteria
            </Alert>
          )
        ) : (
          <Alert severity="info" sx={{ mt: 2 }}>
            No restaurant information available for this city.
          </Alert>
        )}
      </TabPanel>
  
        {/* 景点标签面板 */}
        <TabPanel value={tabValue} index={1}>
        {hasAttractions ? (
          filteredAndSortedPlaces.length > 0 ? (
            <Grid container spacing={3}>
              {filteredAndSortedPlaces.map((place, index) => (
                <Grid item xs={12} sm={6} md={4} key={index} className="place-card">
                  <PlaceCard 
                    place={place} 
                    type="attraction"
                    onSelect={handlePlaceSelect}
                    isSelected={selectedPlaces.some(p => p.place_id === place.place_id)}
                  />
                </Grid>
              ))}
            </Grid>
          ) : (
            <Alert severity="info" sx={{ mt: 2 }}>
              No attractions found matching your criteria
            </Alert>
          )
        ) : (
          <Alert severity="info" sx={{ mt: 2 }}>
            No attraction information available for this city.
          </Alert>
        )}
      </TabPanel>
  
        {/* 酒店标签面板 */}
        <TabPanel value={tabValue} index={2}>
        {hasHotels ? (
          filteredAndSortedPlaces.length > 0 ? (
            <Grid container spacing={3}>
              {filteredAndSortedPlaces.map((place, index) => (
                <Grid item xs={12} sm={6} md={4} key={index} className="place-card">
                  <PlaceCard 
                    place={place} 
                    type="hotel" // 使用当前类型
                    onSelect={handlePlaceSelect}
                    isSelected={selectedPlaces.some(p => p.place_id === place.place_id)}
                    disableAdd={getCurrentType() === 'hotels' && hasSelectedHotel && !selectedPlaces.some(p => p.place_id === place.place_id)}
                  />
                </Grid>
              ))}
            </Grid>
          ) : (
            <Alert severity="info" sx={{ mt: 2 }}>
              No hotels found matching your criteria
            </Alert>
          )
        ) : (
          <Alert severity="info" sx={{ mt: 2 }}>
            No hotel information available for this city.
          </Alert>
        )}
      </TabPanel>
      </Box>
    </Box>
    <PageTour />
  </Box>
  );
};

export default SelectionPage;