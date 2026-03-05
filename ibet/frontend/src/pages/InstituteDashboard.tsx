import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import './Dashboard.css';

export default function InstituteDashboard() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [role, setRole] = useState<'OWNER' | 'TEACHER' | 'STUDENT' | null>(null);
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [activeTab, setActiveTab] = useState('overview');

  // Owner specific states
  const [students, setStudents] = useState<any[]>([]);
  const [teachers, setTeachers] = useState<any[]>([]);
  const [showAddStudent, setShowAddStudent] = useState(false);
  const [isExistingStudent, setIsExistingStudent] = useState(false);
  const [showAddTeacher, setShowAddTeacher] = useState(false);
  const [showMarkPaid, setShowMarkPaid] = useState(false);
  const [showMarkSalaryPaid, setShowMarkSalaryPaid] = useState(false);
  const [showNoticeModal, setShowNoticeModal] = useState(false);
  const [noticeMessage, setNoticeMessage] = useState('');
  const [selectedStudentForNotice, setSelectedStudentForNotice] = useState<any>(null);
  const [showCreateInstitute, setShowCreateInstitute] = useState(false);
  const [showAssignStudents, setShowAssignStudents] = useState(false);
  const [selectedTeacherForAssign, setSelectedTeacherForAssign] = useState<any>(null);
  const [selectedStudentIds, setSelectedStudentIds] = useState<number[]>([]);

  // Attendance states
  const [attendanceDate, setAttendanceDate] = useState(new Date().toLocaleDateString('en-CA')); // YYYY-MM-DD format

  const [attendanceRecords, setAttendanceRecords] = useState<{[key: number]: string}>({});
  const [attendanceReport, setAttendanceReport] = useState<any[]>([]);
  const [attendanceMode, setAttendanceMode] = useState<'mark' | 'report'>('mark');
  
  // Register View States
  const [registerMonth, setRegisterMonth] = useState(new Date().getMonth() + 1);
  const [registerYear, setRegisterYear] = useState(new Date().getFullYear());

  // Form states
  const [newInstitute, setNewInstitute] = useState({ name: '', address: '', contact_number: '' });
  const [newStudent, setNewStudent] = useState({ student_name: '', parent_mobile: '', monthly_fee: '', due_day: '5', institute: '', username: '' });
  const [newTeacher, setNewTeacher] = useState({ username: '', monthly_salary: '', pay_day: '1', institute: '' });
  const [paymentData, setPaymentData] = useState({ student_profile: '', month: new Date().getMonth() + 1, year: new Date().getFullYear(), amount: '' });
  const [salaryData, setSalaryData] = useState({ teacher_profile: '', month: new Date().getMonth() + 1, year: new Date().getFullYear(), amount: '' });

  useEffect(() => {
    loadDashboard();
  }, []);

  useEffect(() => {
    if (activeTab === 'attendance' && (role === 'OWNER' || (role === 'TEACHER' && attendanceMode === 'report'))) {
      fetchAttendanceReport();
    }
  }, [activeTab, attendanceDate, attendanceMode, registerMonth, registerYear]);

  const loadDashboard = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await api.getInstituteDashboard();
      setRole(data.role);
      setDashboardData(data);
      
      if (data.role === 'OWNER' || data.role === 'TEACHER') {
        const [studentList, teacherList] = await Promise.all([
          api.getInstituteStudents(),
          api.getInstituteTeachers()
        ]);
        
        const sData = Array.isArray(studentList) ? studentList : (studentList.results || []);
        const tData = Array.isArray(teacherList) ? teacherList : (teacherList.results || []);
        
        setStudents(sData);
        setTeachers(tData);

        const initialAttendance: {[key: number]: string} = {};
        sData.forEach((s: any) => { initialAttendance[s.id] = 'PRESENT'; });
        setAttendanceRecords(initialAttendance);

        if (data.institutes && data.institutes.length > 0) {
          const instId = data.institutes[0].id;
          setNewStudent(prev => ({ ...prev, institute: instId }));
          setNewTeacher(prev => ({ ...prev, institute: instId }));
        }
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  const fetchAttendanceReport = async () => {
    try {
      const data: any = await api.request(`/institute/attendance/?month=${registerMonth}&year=${registerYear}`);
      setAttendanceReport(Array.isArray(data) ? data : (data.results || []));
    } catch (err) {
      console.error('Failed to fetch attendance report');
    }
  };

  const handleCreateInstitute = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createInstitute(newInstitute);
      setSuccess('Institute created successfully!');
      setShowCreateInstitute(false);
      loadDashboard();
    } catch (err: any) { setError(err.message); }
  };

  const handleUnlinkInstitute = async (id: number) => {
    if (!confirm('Are you sure you want to delete/unlink this institute?')) return;
    try {
      await api.deleteInstitute(id);
      setSuccess('Institute unlinked successfully!');
      loadDashboard();
    } catch (err: any) { setError(err.message); }
  };

  const handleMarkAttendance = async () => {
    setLoading(true);
    try {
      const records = Object.entries(attendanceRecords).map(([id, status]) => ({
        student_profile: parseInt(id),
        status: status
      }));
      await api.markAttendanceBulk(attendanceDate, records);
      setSuccess('Attendance marked successfully!');
      setAttendanceMode('report');
      loadDashboard();
    } catch (err: any) { setError(err.message); } finally { setLoading(false); }
  };

  const handleAddStudent = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      let res;
      console.log('--- ADDING STUDENT ---');
      console.log('Mode:', isExistingStudent ? 'Link Existing' : 'Register New');
      console.log('Payload:', {
        username: newStudent.username,
        institute: newStudent.institute,
        monthly_fee: newStudent.monthly_fee,
        due_day: newStudent.due_day
      });
      
      if (isExistingStudent) {
        res = await api.linkInstituteStudent({
          username: newStudent.username,
          institute: parseInt(newStudent.institute),
          monthly_fee: parseFloat(newStudent.monthly_fee),
          due_day: parseInt(newStudent.due_day)
        });
      } else {
        res = await api.createInstituteStudent(newStudent);
      }
      setSuccess(`${res.message}${res.username ? `. Username: ${res.username}` : ''}`);
      setShowAddStudent(false);
      setIsExistingStudent(false);
      loadDashboard();
    } catch (err: any) { setError(err.message); }
  };

  const handleAddTeacher = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createInstituteTeacher(newTeacher);
      setSuccess('Teacher linked successfully!');
      setShowAddTeacher(false);
      loadDashboard();
    } catch (err: any) { setError(err.message); }
  };

  const handleMarkPaid = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.markFeeAsPaid({
        student_profile: parseInt(paymentData.student_profile),
        month: paymentData.month,
        year: paymentData.year,
        amount: parseFloat(paymentData.amount)
      });
      setSuccess('Fee recorded!');
      setShowMarkPaid(false);
      loadDashboard();
    } catch (err: any) { setError(err.message); }
  };

  const handleMarkSalaryPaid = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.markSalaryAsPaid({
        teacher_profile: parseInt(salaryData.teacher_profile),
        month: salaryData.month,
        year: salaryData.year,
        amount: parseFloat(salaryData.amount)
      });
      setSuccess('Salary recorded!');
      setShowMarkSalaryPaid(false);
      loadDashboard();
    } catch (err: any) { setError(err.message); }
  };

  const handleSendNotice = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedStudentForNotice || !noticeMessage) return;
    try {
      await api.sendInstituteNotice(selectedStudentForNotice.id, noticeMessage);
      setSuccess(`Notice sent to ${selectedStudentForNotice.student_name}`);
      setNoticeMessage('');
      setShowNoticeModal(false);
    } catch (err: any) { setError(err.message); }
  };

  const handleSendFeeReminder = async (studentProfileId: number) => {
    try {
      await api.sendFeeReminder(studentProfileId);
      setSuccess('Reminder sent!');
    } catch (err: any) { setError(err.message); }
  };

  const handleUnlinkStudent = async (id: number) => {
    if (!confirm('Are you sure you want to unlink/remove this student profile?')) return;
    try {
      await api.deleteInstituteStudent(id);
      setSuccess('Student unlinked successfully!');
      loadDashboard();
    } catch (err: any) { setError(err.message); }
  };

  const handleAssignStudents = async () => {
    try {
      await api.request(`/institute/teachers/${selectedTeacherForAssign.id}/`, {
        method: 'PATCH',
        body: JSON.stringify({ assigned_students: selectedStudentIds })
      });
      setSuccess('Students assigned successfully!');
      setShowAssignStudents(false);
      loadDashboard();
    } catch (err: any) { setError(err.message); }
  };

  const toggleStudentSelection = (id: number) => {
    if (selectedStudentIds.includes(id)) {
      setSelectedStudentIds(selectedStudentIds.filter(sid => sid !== id));
    } else {
      setSelectedStudentIds([...selectedStudentIds, id]);
    }
  };

  const handlePayMyFee = async (paymentId: number) => {
    if (!confirm('Proceed with payment?')) return;
    try {
      await api.payFeeSelf(paymentId);
      setSuccess('Payment successful!');
      loadDashboard();
    } catch (err: any) { setError(err.message); }
  };

  const handleLogout = () => { api.clearToken(); navigate('/login'); };

  const getDaysInMonth = (month: number, year: number) => {
    return new Date(year, month, 0).getDate();
  };

  const [showUnlinkModal, setShowUnlinkModal] = useState(false);

  // ... (rest of the component logic)

  if (loading) return <div className="loading">Loading Institute Dashboard...</div>;

  return (
    <div className="dashboard-container">
      <header className="modern-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem 2rem', background: 'white', boxShadow: '0 2px 10px rgba(0,0,0,0.1)', position: 'sticky', top: 0, zIndex: 1000, gap: '1rem' }}>
        <div className="header-section left" style={{ flex: '0 0 120px' }}>
          <button onClick={() => navigate('/select-module')} className="back-btn" style={{ background: 'transparent', color: '#4a5568', border: 'none', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '5px', cursor: 'pointer', padding: 0 }}>
            <span style={{ fontSize: '1.2rem' }}>←</span>
            <span className="hide-mobile">Back</span>
          </button>
        </div>

        <div className="header-section center" style={{ flex: 1, textAlign: 'center', display: 'flex', flexDirection: 'column' }}>
          <h1 className="header-title" style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700, color: '#2c3e50', whiteSpace: 'nowrap' }}>Institute Management 🏫</h1>
          {dashboardData.institutes?.[0] && <span className="header-subtitle" style={{ fontSize: '0.75rem', color: '#7f8c8d', fontWeight: 500, textTransform: 'uppercase' }}>{dashboardData.institutes[0].name}</span>}
        </div>

        <div className="header-section right" style={{ flex: '0 0 auto', display: 'flex', gap: '12px', justifyContent: 'flex-end', alignItems: 'center' }}>
          {role === 'OWNER' && dashboardData.institutes?.[0] && (
            <button 
              onClick={() => setShowUnlinkModal(true)} 
              className="btn-modern btn-danger"
              style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '0.5rem 1rem', borderRadius: '8px', fontSize: '0.85rem', fontWeight: 600, cursor: 'pointer', transition: 'all 0.2s ease', border: '1px solid #feb2b2', background: '#fff5f5', color: '#e74c3c' }}
            >
              <span>🗑️</span>
              <span className="hide-mobile">Unlink</span>
            </button>
          )}
          <button 
            onClick={handleLogout} 
            className="btn-modern btn-secondary"
            style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '0.5rem 1rem', borderRadius: '8px', fontSize: '0.85rem', fontWeight: 600, cursor: 'pointer', transition: 'all 0.2s ease', border: '1px solid #e2e8f0', background: '#f8f9fa', color: '#4a5568' }}
          >
            <span>🚪</span>
            <span className="hide-mobile">Logout</span>
          </button>
        </div>
      </header>

      {/* Confirmation Modal */}
      {showUnlinkModal && (
        <div className="modal-overlay" style={{ display: 'flex', background: 'rgba(0,0,0,0.5)' }}>
          <div className="modal" style={{ maxWidth: '400px' }}>
            <h2 style={{ color: '#e74c3c' }}>Confirm Unlink</h2>
            <p>Are you sure you want to unlink <strong>{dashboardData.institutes[0]?.name}</strong>? This action cannot be easily undone.</p>
            <div style={{ display: 'flex', gap: '10px', marginTop: '1.5rem' }}>
              <button className="submit-btn" style={{ background: '#e74c3c' }} onClick={() => { handleUnlinkInstitute(dashboardData.institutes[0].id); setShowUnlinkModal(false); }}>Yes, Unlink</button>
              <button className="cancel-btn" onClick={() => setShowUnlinkModal(false)}>Cancel</button>
            </div>
          </div>
        </div>
      )}

      {role === 'OWNER' && dashboardData.institutes?.[0] && (
        <div style={{ background: 'rgba(0, 0, 0, 0.05)', padding: '10px 24px', display: 'flex', alignItems: 'center', gap: '10px', color: '#333', borderBottom: '1px solid #eee' }}>
          <span style={{ fontSize: '0.9rem', fontWeight: 'bold' }}>📍 {dashboardData.institutes[0].address}</span>
        </div>
      )}

      <main className="dashboard-main">
        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">{success}</div>}

        {(role === 'OWNER' || role === 'TEACHER') && (
          <>
            <div className="stats-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
              <div className="info-card"><h3>👥 Students</h3><div className="info-value">{role === 'OWNER' ? dashboardData.stats.total_students : students.length}</div></div>
              {role === 'OWNER' && <div className="info-card"><h3>👩‍🏫 Teachers</h3><div className="info-value">{dashboardData.stats.total_teachers}</div></div>}
              {role === 'OWNER' && (
                <>
                  <div className="info-card"><h3>💰 Revenue</h3><div className="info-value" style={{ color: '#2ecc71' }}>₹{dashboardData.stats.monthly_revenue.toFixed(2)}</div></div>
                  <div className="info-card"><h3>📉 Surplus</h3><div className="info-value" style={{ color: '#3498db' }}>₹{dashboardData.stats.net_balance.toFixed(2)}</div></div>
                </>
              )}
            </div>

            <div className="tab-navigation" style={{ marginBottom: '1.5rem' }}>
              <button className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`} onClick={() => setActiveTab('overview')}>Overview</button>
              <button className={`tab-btn ${activeTab === 'attendance' ? 'active' : ''}`} onClick={() => setActiveTab('attendance')}>Attendance</button>
              <button className={`tab-btn ${activeTab === 'students' ? 'active' : ''}`} onClick={() => setActiveTab('students')}>Students</button>
              {role === 'OWNER' && <button className={`tab-btn ${activeTab === 'teachers' ? 'active' : ''}`} onClick={() => setActiveTab('teachers')}>Teachers</button>}
              {role === 'OWNER' && <button className={`tab-btn ${activeTab === 'transactions' ? 'active' : ''}`} onClick={() => setActiveTab('transactions')}>Transactions</button>}
              {role === 'OWNER' && <button className={`tab-btn ${activeTab === 'reports' ? 'active' : ''}`} onClick={() => setActiveTab('reports')}>Reports</button>}
            </div>

            {activeTab === 'overview' && (
              <div className="quick-actions-card info-card">
                <h3>Quick Management</h3>
                <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem', flexWrap: 'wrap' }}>
                  {role === 'OWNER' && <button className="submit-btn" style={{ flex: 1, background: '#3498db' }} onClick={() => setShowCreateInstitute(true)}>🏫 New Institute</button>}
                  <button className="submit-btn" style={{ flex: 1 }} onClick={() => setShowAddStudent(true)}>➕ Add Student</button>
                  {role === 'OWNER' && <button className="submit-btn" style={{ flex: 1 }} onClick={() => setShowAddTeacher(true)}>➕ Add Teacher</button>}
                  {role === 'OWNER' && <button className="submit-btn" style={{ flex: 1, background: '#e67e22' }} onClick={() => setShowMarkPaid(true)}>📝 Record Fee</button>}
                  {role === 'OWNER' && <button className="submit-btn" style={{ flex: 1, background: '#27ae60' }} onClick={() => setShowMarkSalaryPaid(true)}>💵 Pay Salary</button>}
                </div>
              </div>
            )}

            {activeTab === 'attendance' && (
              <div className="info-card" style={{ overflowX: 'auto' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '15px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                    <h3 style={{ margin: 0 }}>Attendance {attendanceMode === 'report' ? 'Register 📜' : 'Marking 📝'}</h3>
                    {role === 'TEACHER' && (
                      <div className="tab-navigation" style={{ marginBottom: 0, padding: '4px', background: '#f0f0f0', borderRadius: '8px' }}>
                        <button className={`tab-btn-small ${attendanceMode === 'mark' ? 'active' : ''}`} onClick={() => setAttendanceMode('mark')} style={{ padding: '4px 12px', fontSize: '0.8rem' }}>Mark</button>
                        <button className={`tab-btn-small ${attendanceMode === 'report' ? 'active' : ''}`} onClick={() => setAttendanceMode('report')} style={{ padding: '4px 12px', fontSize: '0.8rem' }}>Report</button>
                      </div>
                    )}
                  </div>
                  
                  <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                    {(role === 'OWNER' || attendanceMode === 'report') ? (
                      <>
                        <select value={registerMonth} onChange={e => setRegisterMonth(parseInt(e.target.value))} style={{ padding: '6px', borderRadius: '4px' }}>
                          {['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'].map((m, i) => <option key={m} value={i+1}>{m}</option>)}
                        </select>
                        <select value={registerYear} onChange={e => setRegisterYear(parseInt(e.target.value))} style={{ padding: '6px', borderRadius: '4px' }}>
                          {[2025, 2026, 2027].map(y => <option key={y} value={y}>{y}</option>)}
                        </select>
                      </>
                    ) : (
                      <input type="date" value={attendanceDate} onChange={e => setAttendanceDate(e.target.value)} style={{ padding: '0.5rem', borderRadius: '4px', border: '1px solid #ddd' }} />
                    )}
                  </div>
                </div>

                <div className="table-container" style={{ overflowX: 'auto' }}>
                  {(role === 'OWNER' || attendanceMode === 'report') ? (
                    <table className="statement-table attendance-register" style={{ fontSize: '0.8rem', borderCollapse: 'collapse' }}>
                      <thead>
                        <tr>
                          <th style={{ minWidth: '40px', textAlign: 'center' }}>Roll</th>
                          <th style={{ minWidth: '150px' }}>Student Name</th>
                          {Array.from({ length: getDaysInMonth(registerMonth, registerYear) }, (_, i) => (
                            <th key={i+1} style={{ minWidth: '25px', textAlign: 'center', padding: '4px' }}>{i+1}</th>
                          ))}
                          <th style={{ minWidth: '60px', textAlign: 'center', background: '#f9f9f9' }}>Total P</th>
                        </tr>
                      </thead>
                      <tbody>
                        {students.map((s, idx) => {
                          let totalPresent = 0;
                          return (
                            <tr key={s.id}>
                              <td style={{ textAlign: 'center' }}>{idx + 1}</td>
                              <td><strong>{s.student_name}</strong></td>
                              {Array.from({ length: getDaysInMonth(registerMonth, registerYear) }, (_, i) => {
                                const day = i + 1;
                                const dateStr = `${registerYear}-${String(registerMonth).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
                                const record = attendanceReport.find(r => r.student_profile === s.id && r.date === dateStr);
                                let display = '-'; let color = '#ccc';
                                if (record) {
                                  if (record.status === 'PRESENT') { display = 'P'; color = '#27ae60'; totalPresent++; }
                                  else if (record.status === 'ABSENT') { display = 'A'; color = '#e74c3c'; }
                                  else if (record.status === 'LATE') { display = 'L'; color = '#f39c12'; }
                                }
                                return <td key={day} style={{ textAlign: 'center', color, fontWeight: 'bold', border: '1px solid #eee' }}>{display}</td>;
                              })}
                              <td style={{ textAlign: 'center', background: '#f9f9f9', fontWeight: 'bold', color: '#2c3e50' }}>{totalPresent}</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  ) : (
                    <>
                      <table className="statement-table">
                        <thead><tr><th>Student Name</th><th style={{ textAlign: 'right' }}>Status</th></tr></thead>
                        <tbody>
                          {students.map(s => (
                            <tr key={s.id}>
                              <td><strong>{s.student_name}</strong></td>
                              <td style={{ textAlign: 'right' }}>
                                <select value={attendanceRecords[s.id] || 'PRESENT'} onChange={e => setAttendanceRecords({...attendanceRecords, [s.id]: e.target.value})} style={{ padding: '4px', borderRadius: '4px' }}>
                                  <option value="PRESENT">✅ Present</option>
                                  <option value="ABSENT">❌ Absent</option>
                                  <option value="LATE">⏰ Late</option>
                                </select>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                      <button onClick={handleMarkAttendance} className="submit-btn" style={{ marginTop: '1.5rem', background: '#2ecc71' }}>💾 Save Attendance Records</button>
                    </>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'students' && (
              <div className="info-card">
                <h3>Student Directory</h3>
                <div className="table-container" style={{ marginTop: '1rem' }}>
                  <table className="statement-table">
                    <thead><tr><th>Student Name</th><th>Fee Status (Current Month)</th><th>Due</th><th style={{ textAlign: 'right' }}>Actions</th></tr></thead>
                    <tbody>
                      {students.map(s => {
                        const feeStatus = dashboardData.student_fee_status?.[s.id] || { total: parseFloat(s.monthly_fee), paid: 0, pending: parseFloat(s.monthly_fee), status: 'PENDING' };
                        return (
                          <tr key={s.id}>
                            <td><strong>{s.student_name}</strong><br/><small style={{opacity: 0.6}}>User: {s.user_details?.username}</small></td>
                            <td>
                              <div style={{ fontSize: '0.85rem' }}>
                                <div style={{ color: '#555' }}>Total: ₹{feeStatus.total.toFixed(2)}</div>
                                <div style={{ color: '#27ae60', fontWeight: 'bold' }}>Paid: ₹{feeStatus.paid.toFixed(2)}</div>
                                <div style={{ color: feeStatus.pending > 0 ? '#e74c3c' : '#2ecc71', fontWeight: 'bold' }}>Pending: ₹{feeStatus.pending.toFixed(2)}</div>
                              </div>
                            </td>
                            <td>{s.due_day}th</td>
                            <td style={{ textAlign: 'right', display: 'flex', gap: '5px', justifyContent: 'flex-end' }}>
                              <button className="otp-btn-small" style={{ background: '#667eea' }} onClick={() => { setSelectedStudentForNotice(s); setShowNoticeModal(true); }}>📣 Notice</button>
                              <button className="otp-btn-small" onClick={() => handleSendFeeReminder(s.id)}>🔔 Remind</button>
                              <button className="otp-btn-small" style={{ background: '#e74c3c' }} onClick={() => handleUnlinkStudent(s.id)}>🗑️ Unlink</button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {activeTab === 'teachers' && role === 'OWNER' && (
              <div className="info-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h3>Teacher Directory</h3>
                  <button className="submit-btn" style={{ width: 'auto', padding: '0.5rem 1rem' }} onClick={() => setShowAddTeacher(true)}>+ Add Teacher</button>
                </div>
                <div className="table-container" style={{ marginTop: '1rem' }}>
                  <table className="statement-table">
                    <thead><tr><th>Name</th><th>Salary</th><th>Status</th><th style={{ textAlign: 'right' }}>Action</th></tr></thead>
                    <tbody>
                      {teachers.map(t => {
                        const status = dashboardData.teacher_payout_status?.[t.id] || 'PENDING';
                        return (
                          <tr key={t.id}>
                            <td>
                              <strong>{t.user_details?.username}</strong>
                              <br/>
                              <small style={{ color: '#3498db', cursor: 'pointer' }} onClick={() => {
                                setSelectedTeacherForAssign(t);
                                setSelectedStudentIds(t.assigned_students || []);
                                setShowAssignStudents(true);
                              }}>
                                📝 Assign Students ({t.assigned_students?.length || 0})
                              </small>
                            </td>
                            <td>₹{parseFloat(t.monthly_salary).toFixed(2)}</td>
                            <td><span className="tag" style={{ background: status === 'PAID' ? '#e8f5e9' : '#fff3e0', color: status === 'PAID' ? '#2e7d32' : '#e67e22' }}>{status}</span></td>
                            <td style={{ textAlign: 'right' }}>
                              {status === 'PAID' ? (
                                <span style={{ color: '#27ae60', fontSize: '0.85rem', fontWeight: 'bold' }}>✅ Completed</span>
                              ) : (
                                <button className="submit-btn" style={{ width: 'auto', padding: '0.3rem 0.8rem', fontSize: '0.8rem' }} onClick={() => { setSalaryData({...salaryData, teacher_profile: t.id.toString(), amount: t.monthly_salary}); setShowMarkSalaryPaid(true); }}>Pay</button>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {activeTab === 'transactions' && role === 'OWNER' && (
              <div className="info-card">
                <h3>Institute Transaction History 💸</h3>
                <div className="table-container" style={{ marginTop: '1rem' }}>
                  <table className="statement-table">
                    <thead><tr><th>Date</th><th>Type</th><th>Party</th><th>Period</th><th>Amount</th></tr></thead>
                    <tbody>
                      {[
                        ...(dashboardData.recent_paid_fees || []).map((f: any) => ({ ...f, txType: 'INCOME', party: f.student_name || 'Student' })),
                        ...(dashboardData.recent_paid_salaries || []).map((s: any) => ({ ...s, txType: 'EXPENSE', party: s.teacher_name || 'Teacher' }))
                      ].sort((a, b) => new Date(b.payment_date || b.created_at).getTime() - new Date(a.payment_date || a.created_at).getTime()).map((tx, idx) => (
                        <tr key={idx}>
                          <td>{new Date(tx.payment_date || tx.created_at).toLocaleDateString()}</td>
                          <td><span className={`tag ${tx.txType === 'INCOME' ? 'PAID' : 'PENDING'}`} style={{ background: tx.txType === 'INCOME' ? '#e8f5e9' : '#ffebee', color: tx.txType === 'INCOME' ? '#2e7d32' : '#c62828' }}>{tx.txType}</span></td>
                          <td><strong>{tx.party}</strong></td>
                          <td>{tx.month}/{tx.year}</td>
                          <td style={{ color: tx.txType === 'INCOME' ? '#27ae60' : '#e74c3c', fontWeight: 'bold' }}>
                            {tx.txType === 'INCOME' ? '+' : '-'}₹{parseFloat(tx.amount).toFixed(2)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {activeTab === 'reports' && role === 'OWNER' && (
              <div className="balance-card">
                <h2>Monthly Financial Summary 📊</h2>
                <div className="info-cards" style={{ marginTop: '1.5rem' }}>
                  <div className="info-card"><h3>Collected</h3><div className="info-value" style={{ color: '#2ecc71' }}>₹{dashboardData.stats.monthly_revenue.toFixed(2)}</div></div>
                  <div className="info-card"><h3>Salaries Paid</h3><div className="info-value" style={{ color: '#e74c3c' }}>₹{dashboardData.stats.monthly_payout.toFixed(2)}</div></div>
                  <div className="info-card"><h3>Outstanding</h3><div className="info-value" style={{ color: '#e67e22' }}>₹{dashboardData.stats.pending_fees.toFixed(2)}</div></div>
                </div>
              </div>
            )}
          </>
        )}

        {role === 'TEACHER' && activeTab === 'overview' && (
          <div className="teacher-portal">
            {!dashboardData.profile ? (
              <div className="info-card" style={{ textAlign: 'center', padding: '3rem' }}>
                <h2>Welcome, Teacher! 👩‍🏫</h2>
                <p>{dashboardData.message}</p>
              </div>
            ) : (
              <>
                <div className="balance-card">
                  <h2>Teacher Portal 👨‍🏫</h2>
                  <div className="info-cards" style={{ marginTop: '1.5rem' }}>
                    <div className="info-card"><h3>My Monthly Salary</h3><div className="info-value">₹{parseFloat(dashboardData.profile.monthly_salary).toFixed(2)}</div></div>
                    <div className="info-card"><h3>Typical Pay Day</h3><div className="info-value">{dashboardData.profile.pay_day}th</div></div>
                  </div>
                </div>

                <div className="dashboard-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem', marginTop: '2rem' }}>
                  <div className="info-card">
                    <h3>📜 Payout History</h3>
                    <div className="table-container">
                      <table className="statement-table">
                        <thead><tr><th>Period</th><th>Amount</th><th>Status</th></tr></thead>
                        <tbody>
                          {dashboardData.recent_salaries?.map((s: any) => (
                            <tr key={s.id}><td>{s.month}/{s.year}</td><td>₹{parseFloat(s.amount).toFixed(2)}</td><td><span className={`tag ${s.status}`}>{s.status}</span></td></tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                  <div className="info-card">
                    <h3>🔔 Notifications</h3>
                    <div style={{ marginTop: '1rem', maxHeight: '300px', overflowY: 'auto' }}>
                      {dashboardData.notifications?.map((n: any) => (
                        <div key={n.id} style={{ padding: '10px 0', borderBottom: '1px solid #eee', fontSize: '0.85rem' }}><strong>{n.notification_type.replace('_', ' ')}</strong>: {n.message}</div>
                      ))}
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>
        )}

        {role === 'STUDENT' && (
          <div className="student-portal">
            {!dashboardData.profile ? (
              <div className="info-card" style={{ textAlign: 'center', padding: '3rem' }}>
                <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>🎓</div>
                <h2>Parent / Student Portal</h2>
                <p style={{ color: '#666' }}>{dashboardData.message}</p>
              </div>
            ) : (
              <>
                <div className="balance-card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                    <h2 style={{ margin: 0 }}>Parent / Student Portal 🎓</h2>
                    <span style={{ padding: '4px 12px', borderRadius: '20px', background: 'rgba(255,255,255,0.2)', fontSize: '0.9rem', fontWeight: 'bold' }}>{dashboardData.institute_name}</span>
                  </div>
                  <div className="info-cards">
                    <div className="info-card"><h3>Monthly Tuition Fee</h3><div className="info-value">₹{parseFloat(dashboardData.profile.monthly_fee).toFixed(2)}</div></div>
                    <div className="info-card" style={{ borderLeft: `5px solid ${dashboardData.current_fee_status.status === 'PAID' ? '#2ecc71' : '#e74c3c'}` }}>
                      <h3>Status</h3>
                      <div className="info-value" style={{ color: dashboardData.current_fee_status.status === 'PAID' ? '#27ae60' : '#c0392b' }}>{dashboardData.current_fee_status.status}</div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div className="info-sub">{['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][dashboardData.current_fee_status.month-1]} {dashboardData.current_fee_status.year}</div>
                        {dashboardData.current_fee_status.status !== 'PAID' && <button className="submit-btn" style={{ width: 'auto', padding: '0.4rem 1rem', background: '#2ecc71', fontSize: '0.85rem' }} onClick={() => handlePayMyFee(dashboardData.current_fee_status.id)}>💳 Pay Now</button>}
                      </div>
                    </div>
                  </div>
                </div>
                <div className="dashboard-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem', marginTop: '2rem' }}>
                  <div className="info-card">
                    <h3>📅 Recent Attendance</h3>
                    <div style={{ marginTop: '1rem' }}>
                      {dashboardData.attendance?.recent?.map((a: any) => (
                        <div key={a.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid #eee' }}>
                          <span>{new Date(a.date).toLocaleDateString()}</span>
                          <span style={{ fontWeight: 'bold', color: a.status === 'PRESENT' ? '#2ecc71' : '#e74c3c' }}>{a.status}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="info-card">
                    <h3>🔔 Notifications</h3>
                    <div style={{ marginTop: '1rem', maxHeight: '300px', overflowY: 'auto' }}>
                      {dashboardData.notifications?.map((n: any) => (
                        <div key={n.id} style={{ padding: '10px 0', borderBottom: '1px solid #eee', fontSize: '0.85rem' }}><strong>{n.notification_type}</strong>: {n.message}</div>
                      ))}
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>
        )}

        {/* MODALS */}
        {showAssignStudents && (
          <div className="modal-overlay" onClick={() => setShowAssignStudents(false)}>
            <div className="modal" onClick={e => e.stopPropagation()}>
              <h2>Assign Students to {selectedTeacherForAssign?.user_details?.username}</h2>
              <div style={{ maxHeight: '300px', overflowY: 'auto', margin: '1rem 0', border: '1px solid #eee', borderRadius: '8px', padding: '10px' }}>
                {students.map(s => (
                  <div key={s.id} style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '8px', borderBottom: '1px solid #f9f9f9' }}>
                    <input type="checkbox" checked={selectedStudentIds.includes(s.id)} onChange={() => toggleStudentSelection(s.id)} style={{ width: '20px', height: '20px' }} />
                    <span>{s.student_name}</span>
                  </div>
                ))}
              </div>
              <button onClick={handleAssignStudents} className="submit-btn">Save Assignments</button>
              <button onClick={() => setShowAssignStudents(false)} className="cancel-btn">Cancel</button>
            </div>
          </div>
        )}

        {showAddTeacher && (
          <div className="modal-overlay" onClick={() => setShowAddTeacher(false)}>
            <div className="modal" onClick={e => e.stopPropagation()}>
              <h2>Add Teacher 👩‍🏫</h2>
              <form onSubmit={handleAddTeacher}>
                <div className="form-group"><label>Username</label><input type="text" value={newTeacher.username} onChange={e => setNewTeacher({...newTeacher, username: e.target.value})} required /></div>
                <div className="form-group"><label>Monthly Salary</label><input type="number" value={newTeacher.monthly_salary} onChange={e => setNewTeacher({...newTeacher, monthly_salary: e.target.value})} required /></div>
                <button type="submit" className="submit-btn">Link Teacher</button>
                <button type="button" className="cancel-btn" onClick={() => setShowAddTeacher(false)}>Cancel</button>
              </form>
            </div>
          </div>
        )}

        {showAddStudent && (
          <div className="modal-overlay" onClick={() => { setShowAddStudent(false); setIsExistingStudent(false); }}>
            <div className="modal" onClick={e => e.stopPropagation()}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <h2 style={{ margin: 0 }}>Add Student 🎓</h2>
                <div className="tab-navigation" style={{ marginBottom: 0, padding: '4px', background: '#f0f0f0', borderRadius: '8px' }}>
                  <button type="button" className={`tab-btn-small ${!isExistingStudent ? 'active' : ''}`} onClick={() => setIsExistingStudent(false)} style={{ padding: '4px 12px', fontSize: '0.8rem' }}>Register New</button>
                  <button type="button" className={`tab-btn-small ${isExistingStudent ? 'active' : ''}`} onClick={() => setIsExistingStudent(true)} style={{ padding: '4px 12px', fontSize: '0.8rem' }}>Link Existing</button>
                </div>
              </div>

              <form onSubmit={handleAddStudent}>
                {isExistingStudent ? (
                  <>
                    <div className="form-group">
                      <label>Student Username</label>
                      <input 
                        type="text" 
                        value={newStudent.username} 
                        onChange={e => setNewStudent({...newStudent, username: e.target.value})} 
                        placeholder="Enter registered username (e.g. rooban)"
                        required 
                      />
                      <p style={{ fontSize: '0.75rem', color: '#666', marginTop: '4px' }}>The student must already be registered as 'Student (Academic)'</p>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="form-group"><label>Full Name</label><input type="text" value={newStudent.student_name} onChange={e => setNewStudent({...newStudent, student_name: e.target.value})} required /></div>
                    <div className="form-group"><label>Parent Mobile</label><input type="text" value={newStudent.parent_mobile} onChange={e => setNewStudent({...newStudent, parent_mobile: e.target.value})} required /></div>
                  </>
                )}
                <div className="form-group"><label>Monthly Fee (₹)</label><input type="number" value={newStudent.monthly_fee} onChange={e => setNewStudent({...newStudent, monthly_fee: e.target.value})} required /></div>
                <div className="form-group"><label>Due Day (1-31)</label><input type="number" value={newStudent.due_day} onChange={e => setNewStudent({...newStudent, due_day: e.target.value})} required min="1" max="31" /></div>
                <button type="submit" className="submit-btn">{isExistingStudent ? 'Link Student' : 'Register Student'}</button>
                <button type="button" className="cancel-btn" onClick={() => { setShowAddStudent(false); setIsExistingStudent(false); }}>Cancel</button>
              </form>
            </div>
          </div>
        )}

        {showMarkSalaryPaid && (
          <div className="modal-overlay" onClick={() => setShowMarkSalaryPaid(false)}>
            <div className="modal" onClick={e => e.stopPropagation()}>
              <h2>Record Salary Payout 💵</h2>
              <form onSubmit={handleMarkSalaryPaid}>
                <div className="form-group"><label>Teacher</label><select value={salaryData.teacher_profile} onChange={e => setSalaryData({...salaryData, teacher_profile: e.target.value})} required><option value="">-- Choose Teacher --</option>{teachers.map(t => <option key={t.id} value={t.id}>{t.user_details?.username}</option>)}</select></div>
                <div className="form-group"><label>Salary Amount (₹)</label><input type="number" value={salaryData.amount} onChange={e => setSalaryData({...salaryData, amount: e.target.value})} required /></div>
                <button type="submit" className="submit-btn" style={{ background: '#27ae60' }}>Confirm Payout</button>
                <button type="button" className="cancel-btn" onClick={() => setShowMarkSalaryPaid(false)}>Cancel</button>
              </form>
            </div>
          </div>
        )}

        {showMarkPaid && (
          <div className="modal-overlay" onClick={() => setShowMarkPaid(false)}>
            <div className="modal" onClick={e => e.stopPropagation()}>
              <h2>Record Student Fee 📝</h2>
              <form onSubmit={handleMarkPaid}>
                <div className="form-group"><label>Select Student</label><select value={paymentData.student_profile} onChange={e => setPaymentData({...paymentData, student_profile: e.target.value})} required><option value="">-- Choose Student --</option>{students.map(s => <option key={s.id} value={s.id}>{s.student_name}</option>)}</select></div>
                <div className="form-group"><label>Amount Paid (₹)</label><input type="number" value={paymentData.amount} onChange={e => setPaymentData({...paymentData, amount: e.target.value})} required /></div>
                <button type="submit" className="submit-btn">Confirm Payment</button>
                <button type="button" className="cancel-btn" onClick={() => setShowMarkPaid(false)}>Cancel</button>
              </form>
            </div>
          </div>
        )}

        {showCreateInstitute && (
          <div className="modal-overlay" onClick={() => setShowCreateInstitute(false)}>
            <div className="modal" onClick={e => e.stopPropagation()}>
              <h2>Setup Institute 🏫</h2>
              <form onSubmit={handleCreateInstitute}>
                <div className="form-group"><label>Name</label><input type="text" value={newInstitute.name} onChange={e => setNewInstitute({...newInstitute, name: e.target.value})} required /></div>
                <div className="form-group"><label>Address</label><input type="text" value={newInstitute.address} onChange={e => setNewInstitute({...newInstitute, address: e.target.value})} /></div>
                <button type="submit" className="submit-btn">Create</button>
                <button type="button" className="cancel-btn" onClick={() => setShowCreateInstitute(false)}>Cancel</button>
              </form>
            </div>
          </div>
        )}

        {showNoticeModal && (
          <div className="modal-overlay" onClick={() => setShowNoticeModal(false)}>
            <div className="modal" onClick={e => e.stopPropagation()}>
              <h2>Send Official Notice 📣</h2>
              <p style={{ fontSize: '0.9rem', color: '#666', marginBottom: '1rem' }}>To: <strong>{selectedStudentForNotice?.student_name}</strong></p>
              <form onSubmit={handleSendNotice}>
                <div className="form-group">
                  <label>Message</label>
                  <textarea 
                    value={noticeMessage} 
                    onChange={e => setNoticeMessage(e.target.value)} 
                    required 
                    placeholder="Enter your message or reminder here..."
                    style={{ width: '100%', minHeight: '120px', padding: '10px', borderRadius: '8px', border: '1px solid #ddd' }}
                  />
                </div>
                <button type="submit" className="submit-btn" style={{ background: '#667eea' }}>🚀 Send Notice</button>
                <button type="button" className="cancel-btn" onClick={() => setShowNoticeModal(false)}>Cancel</button>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
