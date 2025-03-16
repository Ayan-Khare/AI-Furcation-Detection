import  HomePage  from "./pages/HomePage.jsx"
import Detector from "./pages/Detector.jsx";
import { Route, Routes } from "react-router-dom";
import { Box } from "@chakra-ui/react";

function App() {

  return (
    <Box minH={"100vh"} >
      <Routes>
        <Route path="/" element={<HomePage />}/>
        <Route path="/detect" element={<Detector />}/>
      </Routes>
    </Box>
  )
}

export default App;
