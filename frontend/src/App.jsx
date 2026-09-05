import { Routes, Route, Navigate } from "react-router-dom";

import ProtectedRoute from "./routes/ProtectedRoute";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import AccessDenied from "./pages/AccessDenied";
import Dashboard from "./pages/Dashboard";
import Students from "./pages/Students";
import StudentForm from "./pages/StudentForm";
import StudentProfile from "./pages/StudentProfile";
import Jobs from "./pages/Jobs";
import JobForm from "./pages/JobForm";
import JobDetails from "./pages/JobDetails";
import Analysis from "./pages/Analysis";
import Recommendations from "./pages/Recommendations";
import Applications from "./pages/Applications";
import NotFound from "./pages/NotFound";

function App() {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/access-denied" element={<AccessDenied />} />

      {/* Protected Routes */}

      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<Navigate to="/dashboard" replace />} />

        <Route path="/dashboard" element={<Dashboard />} />

        {/* Students */}

        <Route path="/students" element={<Students />} />

        <Route path="/students/add" element={<StudentForm />} />

        <Route path="/students/:id" element={<StudentProfile />} />

        {/* Jobs */}

        <Route path="/jobs" element={<Jobs />} />

        <Route path="/jobs/add" element={<JobForm />} />

        <Route path="/jobs/:id" element={<JobDetails />} />

        {/* Analysis */}

        <Route path="/analysis" element={<Analysis />} />

        {/* Recommendations */}

        <Route path="/recommendations" element={<Recommendations />} />

        {/* Applications */}

        <Route path="/applications" element={<Applications />} />
      </Route>

      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}

export default App;
