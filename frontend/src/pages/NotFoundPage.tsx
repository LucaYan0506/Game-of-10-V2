import { Link } from "react-router"

function NotFoundPage() {
  return (
    <>
      <div>404 Not Found</div>
      <Link to="/">Back to home</Link>
    </>
  )
}

export default NotFoundPage
