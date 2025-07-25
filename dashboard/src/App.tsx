import { ThemeProvider } from '@mui/material/styles';
import { CssBaseline, Container, AppBar, Toolbar, Typography, Box } from '@mui/material';
import { theme } from './theme';
import AlertList from './components/AlertList';

/**
 * Main App component for the Tarsy Dashboard
 * Provides Material-UI theme, layout structure, and integrates core components
 */
function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Container maxWidth={false} sx={{ px: 2 }}>
        {/* AppBar with dashboard title */}
        <AppBar position="static" elevation={0} sx={{ borderRadius: 1 }}>
          <Toolbar>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              Tarsy Dashboard
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="body2" color="inherit">
                Phase 1 - Basic Alert List
              </Typography>
            </Box>
          </Toolbar>
        </AppBar>

        {/* Main content area */}
        <Box sx={{ mt: 2 }}>
          <AlertList />
        </Box>
      </Container>
    </ThemeProvider>
  );
}

export default App;
