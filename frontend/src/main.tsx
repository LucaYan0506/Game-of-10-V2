import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router'
import './index.css'
import HomePage from './pages/HomePage.tsx'
import NotFoundPage from './pages/NotFoundPage.tsx'

const router = createBrowserRouter([
  {
    path:'/',
    element: <HomePage />,
    errorElement: <NotFoundPage />
  },
  {
    path:'/game/:gameID',
    element: <HomePage />,
  },
]);

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <RouterProvider router={router}/>
  </StrictMode>,
)
