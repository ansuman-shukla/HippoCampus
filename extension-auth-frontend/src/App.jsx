import './index.css'
import { useState, useEffect } from 'react'
import { supabase } from '../supabaseClient'
import { Auth } from '@supabase/auth-ui-react'
import { ThemeSupa } from '@supabase/auth-ui-shared'

function App() {

    const [session, setSession] = useState(null)
    const [isLogged, setIsLogged] = useState(false)

    

    useEffect(() => {
        supabase.auth.getSession().then(({ data: { session } }) => {
          setSession(session)
          console.log(session)
          if (session) {
            localStorage.setItem('session', JSON.stringify(session))
            localStorage.setItem('access_token', session.access_token)
            localStorage.setItem('refresh_token', session.refresh_token)
            
            // Set cookies for the current domain (3904b6d1.hippocampus.pages.dev)
            document.cookie = `access_token=${session.access_token}; path=/; SameSite=Lax; Secure`
            document.cookie = `refresh_token=${session.refresh_token}; path=/; SameSite=Lax; Secure`
            
            // Close the tab after successful authentication
            setTimeout(() => {
              window.close();
            }, 1000);
          }
        })
      
        const {
          data: { subscription },
        } = supabase.auth.onAuthStateChange((_event, session) => {
          console.log('Supabase auth event:', _event);
          setSession(session)
          if (session) {
            localStorage.setItem('session', JSON.stringify(session))
            localStorage.setItem('access_token', session.access_token)
            localStorage.setItem('refresh_token', session.refresh_token)
            
            // Set cookies for the current domain
            document.cookie = `access_token=${session.access_token}; path=/; SameSite=Lax; Secure`
            document.cookie = `refresh_token=${session.refresh_token}; path=/; SameSite=Lax; Secure`
            
            // Close the tab after successful authentication
            setTimeout(() => {
              window.close();
            }, 1000);
          }
        })
      
        return () => subscription.unsubscribe()
      }, [])

    if (!session) {
      return (
        <div style={{ 
          minHeight: '100vh', 
          position: 'relative',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundImage: `url('/generation-4a5900c5-a167-42f7-9d91-7401457f1385 (1).png')`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundRepeat: 'no-repeat'
        }}>
          {/* Overlay for better text visibility */}
          <div style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            backgroundColor: 'rgba(0, 0, 0, 0.05)',
            zIndex: 1
          }}></div>
          
          {/* Auth Container */}
          <div style={{
            position: 'relative',
            zIndex: 2,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '2rem'
          }}>
            <div style={{
              textAlign: 'center',
              maxWidth: '400px'
            }}>
              {/* Auth Component */}
              <Auth
                supabaseClient={supabase}
                appearance={{
                  theme: ThemeSupa,
                  style: {
                    container: {
                      backgroundColor: 'rgba(255, 255, 255, 0.1)',
                      padding: '2rem',
                      borderRadius: '16px',
                      backdropFilter: 'blur(10px)',
                      border: '1px solid rgba(255, 255, 255, 0.2)',
                      boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
                    },
                    button: {
                      backgroundColor: '#ffffff',
                      color: '#333333',
                      padding: '1rem 2rem',
                      borderRadius: '12px',
                      fontWeight: '600',
                      fontSize: '1.1rem',
                      transition: 'all 0.3s ease',
                      border: 'none',
                      width: '100%',
                      marginTop: '1rem',
                      boxShadow: '0 4px 16px rgba(0, 0, 0, 0.2)',
                      cursor: 'pointer'
                    },
                    input: {
                      backgroundColor: 'rgba(255, 255, 255, 0.9)',
                      color: '#333333',
                      borderColor: 'rgba(255, 255, 255, 0.8)',
                      borderRadius: '8px',
                      padding: '0.875rem',
                      width: '100%',
                      marginBottom: '1rem',
                      backdropFilter: 'blur(5px)'
                    },
                    label: {
                      color: '#ffffff',
                      marginBottom: '0.5rem',
                      display: 'block',
                      fontSize: '0.9rem',
                      fontWeight: '500',
                      textShadow: '1px 1px 2px rgba(0, 0, 0, 0.7)'
                    },
                    message: {
                      color: '#ffffff',
                      marginBottom: '1rem',
                      textAlign: 'center',
                      textShadow: '1px 1px 2px rgba(0, 0, 0, 0.7)'
                    }
                  }
                }}
                onlyThirdPartyProviders={true}
                providers={['google']}
              />
            </div>
          </div>
        </div>
      )
    }
    
    else {
      setIsLogged(true)
      if (isLogged) {
        window.close()
      }
      return (<div>Logged in!</div>)
      
      
  }
}


export default App
