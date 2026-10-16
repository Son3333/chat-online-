import React, { useState, useEffect } from 'react';
import { TitleBar } from '../components/TitleBar';
import { Sidebar } from '../features/chat/Sidebar';
import { ChatArea } from '../features/chat/ChatArea';
import { AuthModal } from '../features/auth/AuthModal';
import { CreateGroupModal } from '../features/groups/CreateGroupModal';
import { ContactsModal } from '../features/contacts/ContactsModal';
import { CallModal } from '../features/calls/CallModal';
import { LockScreen } from '../features/security/LockScreen';
import { UpdateModal, UpdateInfo } from '../components/UpdateModal';
import { useChat } from '../context/ChatContext';
import { apiService } from '../services/api';

export const App: React.FC = () => {
  const { currentUser, isLocked, setIsLocked, refreshConversations } = useChat();
  const [showCreateGroup, setShowCreateGroup] = useState(false);
  const [showContacts, setShowContacts] = useState(false);
  const [updateInfo, setUpdateInfo] = useState<UpdateInfo | null>(null);
  const [showUpdateModal, setShowUpdateModal] = useState(false);

  // Listen to 2-second Git updates
  useEffect(() => {
    const unsub = apiService.onUpdateAvailable((info) => {
      setUpdateInfo(info);
      // Không tự ý bật modal đè lên màn hình để tránh làm gián đoạn người dùng
      // Chỉ kích hoạt biểu tượng nháy nháy thông báo trên thanh tiêu đề TitleBar
    });
    return () => unsub();
  }, []);

  // Global keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'l') {
        e.preventDefault();
        setIsLocked(true);
      }
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'r') {
        e.preventDefault();
        refreshConversations();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [setIsLocked, refreshConversations]);

  return (
    <div className="h-screen w-screen flex flex-col bg-slate-100 dark:bg-[#0e1621] overflow-hidden select-none">
      {/* 1. Custom Frameless Titlebar */}
      <TitleBar
        hasUpdateAvailable={Boolean(updateInfo)}
        onOpenUpdateModal={() => setShowUpdateModal(true)}
      />

      {/* 2. Main Workspace Layout */}
      <div className="flex-1 flex overflow-hidden relative">
        <Sidebar
          onOpenCreateGroup={() => setShowCreateGroup(true)}
          onOpenContacts={() => setShowContacts(true)}
        />
        <ChatArea />
      </div>

      {/* 3. Modals and Overlays */}
      {!currentUser && <AuthModal />}
      {isLocked && <LockScreen />}
      <CallModal />

      {showCreateGroup && (
        <CreateGroupModal onClose={() => setShowCreateGroup(false)} />
      )}

      {showContacts && (
        <ContactsModal onClose={() => setShowContacts(false)} />
      )}

      {/* 4. Git Auto-Update Modal (chỉ hiện khi người dùng click vào nút nháy nháy) */}
      {updateInfo && showUpdateModal && (
        <UpdateModal
          updateInfo={updateInfo}
          onDismiss={() => setShowUpdateModal(false)}
        />
      )}
    </div>
  );
};

