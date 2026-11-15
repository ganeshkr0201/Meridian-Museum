import { Link, useLocation } from 'react-router-dom'

const links = [
  { to: '/', label: 'Home' },
  { to: '/plan', label: 'Plan Visit' },
  { to: '/crowd', label: 'Crowd Control' },
  { to: '/memory', label: 'My Profile' },
  { to: '/evaluation', label: 'Evaluation' },
  { to: '/about', label: 'About' },
]

export default function Navbar() {
  const { pathname } = useLocation()
  return (
    <nav className="bg-museum-text text-white shadow-md">
      <div className="max-w-6xl mx-auto px-4 flex items-center justify-between h-14">
        <Link to="/" className="font-display text-lg font-bold tracking-wide text-museum-bg">
          🏛 Meridian Museum
        </Link>
        <div className="flex gap-1 flex-wrap">
          {links.map(l => (
            <Link
              key={l.to}
              to={l.to}
              className={`px-3 py-1 rounded text-sm transition-colors ${
                pathname === l.to
                  ? 'bg-museum-accent text-white'
                  : 'hover:bg-gray-700 text-gray-200'
              }`}
            >
              {l.label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  )
}
